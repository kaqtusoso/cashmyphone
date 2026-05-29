import logging
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

import httpx
from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["orders"])


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


async def _send_to_google_sheet(order: OrderOut) -> IntegrationStatus:
    if not settings.google_sheets_webhook_url:
        return IntegrationStatus(configured=False, ok=True, message="Google Sheets-webhook saknas; hoppade över.")

    try:
        async with httpx.AsyncClient(timeout=settings.order_submission_timeout_seconds) as client:
            response = await client.post(settings.google_sheets_webhook_url, json=_sheet_row(order))
            response.raise_for_status()
        return IntegrationStatus(configured=True, ok=True, message="Order skickad till Google Sheet.")
    except Exception as exc:
        logger.exception("Kunde inte skicka order %s till Google Sheet", order.order_id)
        return IntegrationStatus(configured=True, ok=False, message=str(exc))


def _confirmation_html(order: OrderOut) -> str:
    price = f"{order.price_sek:,}".replace(",", " ")
    return f"""
    <div style="font-family:Arial,sans-serif;color:#111827;line-height:1.5">
      <h1 style="color:#00B87A">Din beställning är mottagen</h1>
      <p>Hej {order.customer.first_name},</p>
      <p>Tack för din order hos CashMyPhone. Vi har registrerat att du vill sälja:</p>
      <ul>
        <li><strong>Ordernummer:</strong> {order.order_id}</li>
        <li><strong>Mobil:</strong> {order.model} {order.storage}</li>
        <li><strong>Köpare:</strong> {order.dealer_name}</li>
        <li><strong>Uppskattat pris:</strong> {price} kr</li>
        <li><strong>Frakt:</strong> {order.shipping_label}</li>
      </ul>
      <h2>Vad händer nu?</h2>
      <p>Vi skickar vidare ordern och fraktinstruktioner följer enligt valt fraktsätt. När mobilen har mottagits och kontrollerats betalas pengarna ut enligt vald betalningsmetod.</p>
      <p>Hälsningar,<br>CashMyPhone</p>
    </div>
    """


async def _send_confirmation_email(order: OrderOut) -> IntegrationStatus:
    if not settings.resend_api_key or not settings.order_email_from:
        return IntegrationStatus(configured=False, ok=True, message="Resend saknar API-nyckel eller avsändare; hoppade över.")

    recipients = [str(order.customer.email)]
    if settings.order_admin_email:
        recipients.append(settings.order_admin_email)

    payload = {
        "from": settings.order_email_from,
        "to": recipients,
        "subject": f"Bekräftelse på din CashMyPhone-order {order.order_id}",
        "html": _confirmation_html(order),
    }

    try:
        async with httpx.AsyncClient(timeout=settings.order_submission_timeout_seconds) as client:
            response = await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {settings.resend_api_key}", "Content-Type": "application/json"},
                json=payload,
            )
            response.raise_for_status()
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
