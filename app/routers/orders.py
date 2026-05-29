import json
import logging
import smtplib
from asyncio import to_thread
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import formataddr
from html import escape
from typing import Any, Literal
from uuid import uuid4

import httpx
from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["orders"])

SHEET_HEADERS = [
    "order_id",
    "created_at",
    "dealer",
    "model",
    "storage",
    "price_sek",
    "shipping",
    "payment",
    "first_name",
    "last_name",
    "personal_number",
    "email",
    "phone",
    "address",
    "postal_code",
    "city",
    "payment_details",
    "condition_answers",
]


class OrderCustomer(BaseModel):
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    personal_number: str = Field(min_length=1)
    address: str = Field(min_length=1)
    postal_code: str = Field(min_length=1)
    city: str = Field(min_length=1)
    phone: str = Field(min_length=1)
    email: str = Field(min_length=3)


class OrderPayment(BaseModel):
    method: str = Field(min_length=1)
    label: str = Field(min_length=1)
    clearing_number: str | None = None
    account_number: str | None = None
    iban_number: str | None = None
    swish_number: str | None = None


class OrderCreate(BaseModel):
    model: str = Field(min_length=1)
    storage: str = Field(min_length=1)
    dealer_id: str = Field(min_length=1)
    dealer_name: str = Field(min_length=1)
    price_sek: int = Field(ge=0)
    shipping_option: str = Field(min_length=1)
    shipping_label: str = Field(min_length=1)
    customer: OrderCustomer
    payment: OrderPayment
    condition_answers: dict[str, Any] | None = None
    source: Literal["cashmyphone_web"] = "cashmyphone_web"


class IntegrationStatus(BaseModel):
    configured: bool
    ok: bool
    message: str


class OrderOut(OrderCreate):
    order_id: str
    created_at: str


class OrderCreateResponse(BaseModel):
    order: OrderOut
    integrations: dict[str, IntegrationStatus]


def _make_order(payload: OrderCreate) -> OrderOut:
    created_at = datetime.now(timezone.utc).isoformat()
    order_id = f"CMP-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid4().hex[:8].upper()}"
    return OrderOut(order_id=order_id, created_at=created_at, **payload.model_dump())


def _sheet_row(order: OrderOut) -> dict[str, Any]:
    return {
        "order_id": order.order_id,
        "created_at": order.created_at,
        "dealer": order.dealer_name,
        "model": order.model,
        "storage": order.storage,
        "price_sek": order.price_sek,
        "shipping": order.shipping_label,
        "payment": order.payment.label,
        "first_name": order.customer.first_name,
        "last_name": order.customer.last_name,
        "personal_number": order.customer.personal_number,
        "email": str(order.customer.email),
        "phone": order.customer.phone,
        "address": order.customer.address,
        "postal_code": order.customer.postal_code,
        "city": order.customer.city,
        "payment_details": {
            "clearing_number": order.payment.clearing_number,
            "account_number": order.payment.account_number,
            "iban_number": order.payment.iban_number,
            "swish_number": order.payment.swish_number,
        },
        "condition_answers": order.condition_answers,
    }


def _sheet_values(order: OrderOut) -> list[Any]:
    row = _sheet_row(order)
    values: list[Any] = []
    for key in SHEET_HEADERS:
        value = row.get(key)
        if isinstance(value, (dict, list)):
            values.append(json.dumps(value, ensure_ascii=False))
        elif value is None:
            values.append("")
        else:
            values.append(value)
    return values


def _load_service_account_info() -> dict[str, Any]:
    raw = settings.google_service_account_json.strip()
    if not raw:
        raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON saknas")

    try:
        info = json.loads(raw)
    except json.JSONDecodeError:
        # Railway values sometimes get pasted with extra surrounding quotes.
        info = json.loads(raw.strip("'\""))

    private_key = info.get("private_key")
    if isinstance(private_key, str) and "\\n" in private_key:
        info["private_key"] = private_key.replace("\\n", "\n")

    return info


async def _get_google_access_token() -> str:
    from google.auth.transport.requests import Request
    from google.oauth2.service_account import Credentials

    credentials = Credentials.from_service_account_info(
        _load_service_account_info(),
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    credentials.refresh(Request())
    return credentials.token


async def _ensure_google_sheet_headers(client: httpx.AsyncClient, token: str) -> None:
    sheet_name = settings.google_sheets_worksheet_name
    spreadsheet_id = settings.google_sheets_spreadsheet_id
    encoded_range = httpx.URL(f"https://example.com/{sheet_name}!1:1").raw_path.decode().lstrip("/")
    base_url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values"
    headers = {"Authorization": f"Bearer {token}"}

    get_response = await client.get(f"{base_url}/{encoded_range}", headers=headers)
    get_response.raise_for_status()
    existing_values = get_response.json().get("values", [])
    if existing_values:
        return

    update_response = await client.put(
        f"{base_url}/{encoded_range}",
        params={"valueInputOption": "RAW"},
        headers=headers,
        json={"values": [SHEET_HEADERS]},
    )
    update_response.raise_for_status()


async def _send_to_google_sheet_api(order: OrderOut) -> IntegrationStatus:
    if not settings.google_service_account_json or not settings.google_sheets_spreadsheet_id:
        return IntegrationStatus(
            configured=False,
            ok=True,
            message="Google Sheets API saknar service account JSON eller spreadsheet ID; hoppade över.",
        )

    try:
        token = await _get_google_access_token()
        sheet_name = settings.google_sheets_worksheet_name
        spreadsheet_id = settings.google_sheets_spreadsheet_id
        encoded_range = httpx.URL(f"https://example.com/{sheet_name}!A:R").raw_path.decode().lstrip("/")

        async with httpx.AsyncClient(timeout=settings.order_submission_timeout_seconds) as client:
            await _ensure_google_sheet_headers(client, token)
            response = await client.post(
                f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{encoded_range}:append",
                params={"valueInputOption": "USER_ENTERED", "insertDataOption": "INSERT_ROWS"},
                headers={"Authorization": f"Bearer {token}"},
                json={"values": [_sheet_values(order)]},
            )
            response.raise_for_status()

        return IntegrationStatus(configured=True, ok=True, message="Order skickad till Google Sheet via Sheets API.")
    except Exception as exc:
        logger.exception("Kunde inte skicka order %s till Google Sheets API", order.order_id)
        return IntegrationStatus(configured=True, ok=False, message=str(exc))


async def _send_to_google_sheet_webhook(order: OrderOut) -> IntegrationStatus:
    if not settings.google_sheets_webhook_url:
        return IntegrationStatus(configured=False, ok=True, message="Google Sheets-webhook saknas; hoppade över.")

    try:
        async with httpx.AsyncClient(timeout=settings.order_submission_timeout_seconds) as client:
            response = await client.post(settings.google_sheets_webhook_url, json=_sheet_row(order))
            response.raise_for_status()
        return IntegrationStatus(configured=True, ok=True, message="Order skickad till Google Sheet via webhook.")
    except Exception as exc:
        logger.exception("Kunde inte skicka order %s till Google Sheet-webhook", order.order_id)
        return IntegrationStatus(configured=True, ok=False, message=str(exc))


async def _send_to_google_sheet(order: OrderOut) -> IntegrationStatus:
    api_status = await _send_to_google_sheet_api(order)
    if api_status.configured or not settings.google_sheets_webhook_url:
        return api_status

    return await _send_to_google_sheet_webhook(order)


def _confirmation_html(order: OrderOut) -> str:
    price = f"{order.price_sek:,}".replace(",", " ")
    customer_name = escape(order.customer.first_name)
    order_id = escape(order.order_id)
    model = escape(order.model)
    storage = escape(order.storage)
    dealer_name = escape(order.dealer_name)
    shipping_label = escape(order.shipping_label)
    payment_label = escape(order.payment.label)

    return f"""
    <div style="font-family:Arial,sans-serif;color:#111827;line-height:1.5">
      <h1 style="color:#00B87A">Din beställning är mottagen</h1>
      <p>Hej {customer_name},</p>
      <p>Tack för din order hos CashMyPhone. Vi har registrerat att du vill sälja:</p>
      <ul>
        <li><strong>Ordernummer:</strong> {order_id}</li>
        <li><strong>Mobil:</strong> {model} {storage}</li>
        <li><strong>Köpare:</strong> {dealer_name}</li>
        <li><strong>Uppskattat pris:</strong> {price} kr</li>
        <li><strong>Frakt:</strong> {shipping_label}</li>
        <li><strong>Betalning:</strong> {payment_label}</li>
      </ul>
      <h2>Vad händer nu?</h2>
      <p>Du får fraktinstruktioner och skickar mobilen när du är redo. {dealer_name} kontrollerar mobilen och betalar ut enligt valt betalningssätt.</p>
      <p>Hälsningar,<br>CashMyPhone</p>
    </div>
    """


def _confirmation_text(order: OrderOut) -> str:
    price = f"{order.price_sek:,}".replace(",", " ")
    return f"""Hej {order.customer.first_name},

Tack för din order hos CashMyPhone.

Ordernummer: {order.order_id}
Mobil: {order.model} {order.storage}
Köpare: {order.dealer_name}
Uppskattat pris: {price} kr
Frakt: {order.shipping_label}
Betalning: {order.payment.label}

Vad händer nu?
Du får fraktinstruktioner och skickar mobilen när du är redo. {order.dealer_name} kontrollerar mobilen och betalar ut enligt valt betalningssätt.

Hälsningar,
CashMyPhone
"""


def _build_confirmation_email(order: OrderOut) -> EmailMessage:
    from_email = settings.smtp_from_email or settings.order_email_from
    from_name = settings.smtp_from_name or "CashMyPhone"

    message = EmailMessage()
    message["From"] = formataddr((from_name, from_email))
    message["To"] = str(order.customer.email)
    if settings.order_admin_email:
        message["Bcc"] = settings.order_admin_email
    if settings.smtp_reply_to:
        message["Reply-To"] = settings.smtp_reply_to
    message["Subject"] = f"Bekräftelse på din CashMyPhone-order {order.order_id}"
    message.set_content(_confirmation_text(order))
    message.add_alternative(_confirmation_html(order), subtype="html")
    return message


def _send_confirmation_email_sync(order: OrderOut) -> None:
    message = _build_confirmation_email(order)
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=settings.order_submission_timeout_seconds) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message)


async def _send_confirmation_email(order: OrderOut) -> IntegrationStatus:
    from_email = settings.smtp_from_email or settings.order_email_from
    if not settings.smtp_host or not settings.smtp_username or not settings.smtp_password or not from_email:
        return IntegrationStatus(configured=False, ok=True, message="SMTP saknar host, login, lösenord eller avsändare; hoppade över.")

    try:
        await to_thread(_send_confirmation_email_sync, order)
        return IntegrationStatus(configured=True, ok=True, message="Bekräftelsemail skickat.")
    except Exception as exc:
        logger.exception("Kunde inte skicka ordermail för %s", order.order_id)
        return IntegrationStatus(configured=True, ok=False, message=str(exc))


@router.post("/orders", response_model=OrderCreateResponse)
async def create_order(payload: OrderCreate):
    order = _make_order(payload)
    sheets_status = await _send_to_google_sheet(order)
    email_status = await _send_confirmation_email(order)

    return OrderCreateResponse(
        order=order,
        integrations={
            "google_sheets": sheets_status,
            "email": email_status,
        },
    )
