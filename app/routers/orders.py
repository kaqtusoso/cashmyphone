import json
import logging
import smtplib
from asyncio import create_task, gather, to_thread
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import formataddr
from html import escape
from typing import Any, Literal
from uuid import uuid4

import httpx
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from ..config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["orders"])

SHEET_COLUMNS = [
    ("order_id", "Ordernummer", 190),
    ("created_at", "Datum", 170),
    ("dealer", "Köpare", 130),
    ("model", "Modell", 170),
    ("storage", "Lagring", 95),
    ("price_sek", "Pris (SEK)", 105),
    ("shipping", "Frakt", 190),
    ("payment", "Betalning", 120),
    ("first_name", "Förnamn", 120),
    ("last_name", "Efternamn", 130),
    ("personal_number", "Personnummer", 145),
    ("email", "E-post", 220),
    ("phone", "Telefon", 140),
    ("address", "Adress", 180),
    ("postal_code", "Postnummer", 110),
    ("city", "Ort", 130),
    ("payment_details", "Betalningsuppgifter", 230),
    ("condition_answers", "Skick / frågesvar", 380),
]
SHEET_KEYS = [key for key, _, _ in SHEET_COLUMNS]
SHEET_HEADERS = [header for _, header, _ in SHEET_COLUMNS]
SHEET_HEADER_TO_KEY = {header: key for key, header, _ in SHEET_COLUMNS}


class OrderCustomer(BaseModel):
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    personal_number: str | None = None
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
    client_order_id: str | None = None
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
    source: Literal["televera_web"] = "televera_web"


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
    order_id = payload.client_order_id or f"TLV-{uuid4().hex[:10].upper()}"
    return OrderOut(order_id=order_id, created_at=created_at, **payload.model_dump())


def _format_sheet_datetime(value: str) -> str:
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return value
    return dt.strftime("%Y-%m-%d %H:%M")


def _format_payment_details(payment: OrderPayment) -> str:
    if payment.method == "swish" and payment.swish_number:
        return f"Swish: {payment.swish_number}"

    details = []
    if payment.clearing_number:
        details.append(f"Clearing: {payment.clearing_number}")
    if payment.account_number:
        details.append(f"Konto: {payment.account_number}")
    if payment.iban_number:
        details.append(f"IBAN: {payment.iban_number}")
    return "\n".join(details)


def _format_condition_answers(condition_answers: dict[str, Any] | None) -> str:
    if not condition_answers:
        return ""

    labels = {
        "batteryHealth": "Batterihälsa",
        "screenGlass": "Skärmglas",
        "screenWear": "Skärmskick",
        "sidesWear": "Sidor",
        "backWear": "Baksida",
        "screenFunctionAnswered": "Skärmtest besvarat",
    }
    value_labels = {
        "chipped": "Sprickor/flisor",
        "scratched": "Repor",
        "none": "Inga skador",
        "visible": "Tydligt slitage",
        "some": "Visst slitage",
        "minimal": "Minimalt slitage",
        "cracked": "Sprucken",
    }
    functional_labels = {
        "powersOn": "Startar normalt",
        "network": "Nätverk fungerar",
        "faceId": "Face ID fungerar",
        "selfieCamera": "Selfiekamera fungerar",
        "speaker": "Högtalare fungerar",
        "bentOrWaterDamaged": "Böjd/vattenskadad",
    }

    rows: list[str] = []
    for key in ("batteryHealth", "screenGlass", "screenWear", "sidesWear", "backWear"):
        value = condition_answers.get(key)
        if value is None:
            continue
        formatted_value = f"{value}%" if key == "batteryHealth" else value_labels.get(str(value), str(value))
        rows.append(f"{labels[key]}: {formatted_value}")

    functional = condition_answers.get("functional")
    if isinstance(functional, dict):
        for key, label in functional_labels.items():
            value = functional.get(key)
            if value is None:
                continue
            rows.append(f"{label}: {'Ja' if value else 'Nej'}")

    screen_function = condition_answers.get("screenFunction")
    if isinstance(screen_function, dict):
        issues = [
            label
            for key, label in (
                ("brightSpots", "Ljusa fläckar"),
                ("deadPixels", "Döda pixlar"),
                ("linesOrBurnIn", "Linjer/inbränning"),
            )
            if screen_function.get(key)
        ]
        rows.append(f"Skärmfunktion: {', '.join(issues) if issues else 'OK'}")

    return "\n".join(rows)


def _sheet_row(order: OrderOut) -> dict[str, Any]:
    return {
        "order_id": order.order_id,
        "created_at": _format_sheet_datetime(order.created_at),
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
        "payment_details": _format_payment_details(order.payment),
        "condition_answers": _format_condition_answers(order.condition_answers),
    }


def _sheet_values(order: OrderOut) -> list[Any]:
    row = _sheet_row(order)
    values: list[Any] = []
    for key in SHEET_KEYS:
        value = row.get(key)
        if isinstance(value, (dict, list)):
            values.append(json.dumps(value, ensure_ascii=False))
        elif value is None:
            values.append("")
        else:
            values.append(value)
    return values


def _normalize_existing_sheet_row(headers: list[str], row: list[Any]) -> list[Any]:
    mapped: dict[str, Any] = {}
    for index, header in enumerate(headers):
        key = header if header in SHEET_KEYS else SHEET_HEADER_TO_KEY.get(header)
        if key:
            mapped[key] = row[index] if index < len(row) else ""

    if mapped.get("created_at"):
        mapped["created_at"] = _format_sheet_datetime(str(mapped["created_at"]))

    payment_details = mapped.get("payment_details")
    if isinstance(payment_details, str):
        try:
            parsed = json.loads(payment_details)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict):
            mapped["payment_details"] = _format_payment_details(OrderPayment(method="bank", label="Banköverföring", **parsed))

    condition_answers = mapped.get("condition_answers")
    if isinstance(condition_answers, str):
        try:
            parsed = json.loads(condition_answers)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict):
            mapped["condition_answers"] = _format_condition_answers(parsed)

    return [mapped.get(key, "") for key in SHEET_KEYS]


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


async def _get_google_sheet_id(client: httpx.AsyncClient, token: str) -> int:
    sheet_name = settings.google_sheets_worksheet_name
    spreadsheet_id = settings.google_sheets_spreadsheet_id
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get(
        f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}",
        params={"fields": "sheets(properties(sheetId,title))"},
        headers=headers,
    )
    response.raise_for_status()

    for sheet in response.json().get("sheets", []):
        properties = sheet.get("properties", {})
        if properties.get("title") == sheet_name:
            return int(properties["sheetId"])

    raise ValueError(f"Worksheet '{sheet_name}' saknas i Google Sheet.")


def _google_sheet_data_row_format() -> dict[str, Any]:
    return {
        "backgroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0},
        "horizontalAlignment": "LEFT",
        "verticalAlignment": "MIDDLE",
        "wrapStrategy": "CLIP",
        "textFormat": {
            "foregroundColor": {"red": 0.08, "green": 0.1, "blue": 0.15},
            "bold": False,
            "fontSize": 10,
        },
    }


def _google_sheet_data_row_format_fields() -> str:
    return "userEnteredFormat(backgroundColor,horizontalAlignment,verticalAlignment,wrapStrategy,textFormat)"


def _range_end_row(range_name: str) -> int | None:
    _, _, cell_range = range_name.partition("!")
    if not cell_range:
        return None

    end_ref = cell_range.split(":")[-1]
    digits = "".join(char for char in end_ref if char.isdigit())
    return int(digits) if digits else None


async def _format_google_sheet(client: httpx.AsyncClient, token: str, sheet_id: int) -> None:
    spreadsheet_id = settings.google_sheets_spreadsheet_id
    column_count = len(SHEET_COLUMNS)
    requests: list[dict[str, Any]] = [
        {
            "updateSheetProperties": {
                "properties": {
                    "sheetId": sheet_id,
                    "gridProperties": {"frozenRowCount": 1},
                },
                "fields": "gridProperties.frozenRowCount",
            }
        },
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 0,
                    "endRowIndex": 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": column_count,
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.0, "green": 0.45, "blue": 0.31},
                        "horizontalAlignment": "CENTER",
                        "verticalAlignment": "MIDDLE",
                        "wrapStrategy": "WRAP",
                        "textFormat": {
                            "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0},
                            "bold": True,
                            "fontSize": 11,
                        },
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)",
            }
        },
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": column_count,
                },
                "cell": {"userEnteredFormat": _google_sheet_data_row_format()},
                "fields": _google_sheet_data_row_format_fields(),
            }
        },
        {
            "updateDimensionProperties": {
                "range": {
                    "sheetId": sheet_id,
                    "dimension": "ROWS",
                    "startIndex": 1,
                },
                "properties": {"pixelSize": 21},
                "fields": "pixelSize",
            }
        },
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 1,
                    "startColumnIndex": 5,
                    "endColumnIndex": 6,
                },
                "cell": {
                    "userEnteredFormat": {
                        "numberFormat": {"type": "NUMBER", "pattern": '#,##0 "kr"'},
                        "horizontalAlignment": "RIGHT",
                    }
                },
                "fields": "userEnteredFormat(numberFormat,horizontalAlignment)",
            }
        },
        {
            "setBasicFilter": {
                "filter": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 0,
                        "startColumnIndex": 0,
                        "endColumnIndex": column_count,
                    }
                }
            }
        },
    ]

    for index, (_, _, width) in enumerate(SHEET_COLUMNS):
        requests.append(
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": sheet_id,
                        "dimension": "COLUMNS",
                        "startIndex": index,
                        "endIndex": index + 1,
                    },
                    "properties": {"pixelSize": width},
                    "fields": "pixelSize",
                }
            }
        )

    response = await client.post(
        f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}:batchUpdate",
        headers={"Authorization": f"Bearer {token}"},
        json={"requests": requests},
    )
    response.raise_for_status()


async def _ensure_google_sheet_layout(client: httpx.AsyncClient, token: str) -> None:
    sheet_name = settings.google_sheets_worksheet_name
    spreadsheet_id = settings.google_sheets_spreadsheet_id
    encoded_range = httpx.URL(f"https://example.com/{sheet_name}!1:1").raw_path.decode().lstrip("/")
    base_url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values"
    headers = {"Authorization": f"Bearer {token}"}
    sheet_id = await _get_google_sheet_id(client, token)

    get_response = await client.get(f"{base_url}/{encoded_range}", headers=headers)
    get_response.raise_for_status()
    existing_values = get_response.json().get("values", [])

    if not existing_values or existing_values[0] != SHEET_HEADERS:
        update_response = await client.put(
            f"{base_url}/{encoded_range}",
            params={"valueInputOption": "RAW"},
            headers=headers,
            json={"values": [SHEET_HEADERS]},
        )
        update_response.raise_for_status()

    await _format_google_sheet(client, token, sheet_id)


async def _rebuild_google_sheet(client: httpx.AsyncClient, token: str) -> None:
    sheet_name = settings.google_sheets_worksheet_name
    spreadsheet_id = settings.google_sheets_spreadsheet_id
    encoded_range = httpx.URL(f"https://example.com/{sheet_name}!A:R").raw_path.decode().lstrip("/")
    base_url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values"
    headers = {"Authorization": f"Bearer {token}"}
    sheet_id = await _get_google_sheet_id(client, token)

    get_response = await client.get(f"{base_url}/{encoded_range}", headers=headers)
    get_response.raise_for_status()
    existing_values = get_response.json().get("values", [])

    rows: list[list[Any]] = [SHEET_HEADERS]
    if existing_values:
        source_headers = existing_values[0]
        for row in existing_values[1:]:
            if any(str(cell).strip() for cell in row):
                rows.append(_normalize_existing_sheet_row(source_headers, row))

    clear_response = await client.post(f"{base_url}/{encoded_range}:clear", headers=headers, json={})
    clear_response.raise_for_status()

    update_response = await client.put(
        f"{base_url}/{encoded_range}",
        params={"valueInputOption": "USER_ENTERED"},
        headers=headers,
        json={"values": rows},
    )
    update_response.raise_for_status()

    await _format_google_sheet(client, token, sheet_id)


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
            await _ensure_google_sheet_layout(client, token)
            response = await client.post(
                f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{encoded_range}:append",
                params={"valueInputOption": "USER_ENTERED", "insertDataOption": "INSERT_ROWS"},
                headers={"Authorization": f"Bearer {token}"},
                json={"values": [_sheet_values(order)]},
            )
            response.raise_for_status()
            updated_range = response.json().get("updates", {}).get("updatedRange", "")
            updated_end_row = _range_end_row(updated_range)
            if updated_end_row:
                format_response = await client.post(
                    f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}:batchUpdate",
                    headers={"Authorization": f"Bearer {token}"},
                    json={
                        "requests": [
                            {
                                "repeatCell": {
                                    "range": {
                                        "sheetId": sheet_id,
                                        "startRowIndex": updated_end_row - 1,
                                        "endRowIndex": updated_end_row,
                                        "startColumnIndex": 0,
                                        "endColumnIndex": len(SHEET_COLUMNS),
                                    },
                                    "cell": {"userEnteredFormat": _google_sheet_data_row_format()},
                                    "fields": _google_sheet_data_row_format_fields(),
                                }
                            },
                            {
                                "repeatCell": {
                                    "range": {
                                        "sheetId": sheet_id,
                                        "startRowIndex": updated_end_row - 1,
                                        "endRowIndex": updated_end_row,
                                        "startColumnIndex": 5,
                                        "endColumnIndex": 6,
                                    },
                                    "cell": {
                                        "userEnteredFormat": {
                                            "numberFormat": {"type": "NUMBER", "pattern": '#,##0 "kr"'},
                                            "horizontalAlignment": "RIGHT",
                                        }
                                    },
                                    "fields": "userEnteredFormat(numberFormat,horizontalAlignment)",
                                }
                            },
                        ]
                    },
                )
                format_response.raise_for_status()

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


def _google_sheet_is_configured() -> bool:
    return bool(
        (settings.google_service_account_json and settings.google_sheets_spreadsheet_id)
        or settings.google_sheets_webhook_url
    )


@router.post("/orders/sheets/layout", response_model=IntegrationStatus)
async def refresh_order_sheet_layout(x_api_key: str = Header(..., alias="X-API-Key")):
    if x_api_key != settings.scrape_api_key:
        raise HTTPException(status_code=401, detail="Ogiltig API-nyckel")

    if not settings.google_service_account_json or not settings.google_sheets_spreadsheet_id:
        return IntegrationStatus(
            configured=False,
            ok=False,
            message="Google Sheets API saknar service account JSON eller spreadsheet ID.",
        )

    try:
        token = await _get_google_access_token()
        async with httpx.AsyncClient(timeout=settings.order_submission_timeout_seconds) as client:
            await _rebuild_google_sheet(client, token)
        return IntegrationStatus(configured=True, ok=True, message="Orderarket har formaterats.")
    except Exception as exc:
        logger.exception("Kunde inte formatera orderarket")
        return IntegrationStatus(configured=True, ok=False, message=str(exc))


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
    <!doctype html>
    <html lang="sv">
      <body style="margin:0;padding:0;background:#f4f7f5;color:#17211c;font-family:Arial,'Helvetica Neue',Helvetica,sans-serif;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f4f7f5;margin:0;padding:28px 12px;">
          <tr>
            <td align="center">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:640px;background:#ffffff;border-radius:18px;overflow:hidden;border:1px solid #dfe7e2;box-shadow:0 10px 34px rgba(23,33,28,0.08);">
                <tr>
                  <td style="background:#073d2b;padding:26px 28px;color:#ffffff;">
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                      <tr>
                        <td>
                          <div style="font-size:24px;font-weight:800;letter-spacing:0;color:#ffffff;">Televera</div>
                          <div style="margin-top:6px;font-size:14px;line-height:20px;color:#bfe9d7;">Orderbekräftelse</div>
                        </td>
                        <td align="right" style="vertical-align:top;">
                          <span style="display:inline-block;background:#00b87a;color:#073d2b;border-radius:999px;padding:7px 12px;font-size:13px;font-weight:700;">Mottagen</span>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>

                <tr>
                  <td style="padding:30px 28px 12px;">
                    <h1 style="margin:0 0 12px;font-size:28px;line-height:34px;color:#10271f;font-weight:800;">Tack {customer_name}, vi har tagit emot din order.</h1>
                    <p style="margin:0;color:#54635d;font-size:16px;line-height:25px;">Vi har registrerat att du vill sälja din <strong style="color:#17211c;">{model} {storage}</strong>. Spara ordernumret nedan om du behöver kontakta oss.</p>
                  </td>
                </tr>

                <tr>
                  <td style="padding:18px 28px 8px;">
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f0fbf6;border:1px solid #bdebd6;border-radius:14px;">
                      <tr>
                        <td style="padding:18px 18px;">
                          <div style="font-size:13px;text-transform:uppercase;color:#4f6b5f;font-weight:700;letter-spacing:.04em;">Ordernummer</div>
                          <div style="margin-top:6px;font-size:22px;line-height:28px;color:#073d2b;font-weight:800;">{order_id}</div>
                        </td>
                        <td align="right" style="padding:18px 18px;">
                          <div style="font-size:13px;text-transform:uppercase;color:#4f6b5f;font-weight:700;letter-spacing:.04em;">Uppskattat pris</div>
                          <div style="margin-top:6px;font-size:24px;line-height:30px;color:#00a66f;font-weight:800;">{price} kr</div>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>

                <tr>
                  <td style="padding:16px 28px 8px;">
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border-collapse:collapse;">
                      <tr>
                        <td style="padding:13px 0;border-bottom:1px solid #edf2ef;color:#63716b;font-size:14px;">Mobil</td>
                        <td align="right" style="padding:13px 0;border-bottom:1px solid #edf2ef;color:#17211c;font-size:15px;font-weight:700;">{model} {storage}</td>
                      </tr>
                      <tr>
                        <td style="padding:13px 0;border-bottom:1px solid #edf2ef;color:#63716b;font-size:14px;">Köpare</td>
                        <td align="right" style="padding:13px 0;border-bottom:1px solid #edf2ef;color:#17211c;font-size:15px;font-weight:700;">{dealer_name}</td>
                      </tr>
                      <tr>
                        <td style="padding:13px 0;border-bottom:1px solid #edf2ef;color:#63716b;font-size:14px;">Frakt</td>
                        <td align="right" style="padding:13px 0;border-bottom:1px solid #edf2ef;color:#17211c;font-size:15px;font-weight:700;">{shipping_label}</td>
                      </tr>
                      <tr>
                        <td style="padding:13px 0;color:#63716b;font-size:14px;">Betalning</td>
                        <td align="right" style="padding:13px 0;color:#17211c;font-size:15px;font-weight:700;">{payment_label}</td>
                      </tr>
                    </table>
                  </td>
                </tr>

                <tr>
                  <td style="padding:20px 28px 26px;">
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#fbfcfb;border:1px solid #e5ece8;border-radius:14px;">
                      <tr>
                        <td style="padding:20px 20px;">
                          <h2 style="margin:0 0 14px;font-size:20px;line-height:26px;color:#10271f;">Vad händer nu?</h2>
                          <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                            <tr>
                              <td width="30" style="vertical-align:top;padding:0 0 12px;">
                                <div style="width:22px;height:22px;border-radius:999px;background:#00b87a;color:#ffffff;text-align:center;line-height:22px;font-size:13px;font-weight:700;">1</div>
                              </td>
                              <td style="padding:0 0 12px;color:#54635d;font-size:15px;line-height:22px;">Du får fraktinstruktioner och skickar mobilen när du är redo.</td>
                            </tr>
                            <tr>
                              <td width="30" style="vertical-align:top;padding:0 0 12px;">
                                <div style="width:22px;height:22px;border-radius:999px;background:#00b87a;color:#ffffff;text-align:center;line-height:22px;font-size:13px;font-weight:700;">2</div>
                              </td>
                              <td style="padding:0 0 12px;color:#54635d;font-size:15px;line-height:22px;">{dealer_name} kontrollerar mobilen när den kommit fram.</td>
                            </tr>
                            <tr>
                              <td width="30" style="vertical-align:top;">
                                <div style="width:22px;height:22px;border-radius:999px;background:#00b87a;color:#ffffff;text-align:center;line-height:22px;font-size:13px;font-weight:700;">3</div>
                              </td>
                              <td style="color:#54635d;font-size:15px;line-height:22px;">Utbetalning görs enligt ditt valda betalningssätt.</td>
                            </tr>
                          </table>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>

                <tr>
                  <td style="padding:0 28px 30px;color:#63716b;font-size:14px;line-height:22px;">
                    Hälsningar,<br>
                    <strong style="color:#17211c;">Televera</strong>
                  </td>
                </tr>
              </table>
              <div style="max-width:640px;margin:16px auto 0;color:#7a8882;font-size:12px;line-height:18px;text-align:center;">
                Detta är en automatisk orderbekräftelse från Televera.
              </div>
            </td>
          </tr>
        </table>
      </body>
    </html>
    """


def _confirmation_text(order: OrderOut) -> str:
    price = f"{order.price_sek:,}".replace(",", " ")
    return f"""Hej {order.customer.first_name},

Tack för din order hos Televera.

Ordernummer: {order.order_id}
Mobil: {order.model} {order.storage}
Köpare: {order.dealer_name}
Uppskattat pris: {price} kr
Frakt: {order.shipping_label}
Betalning: {order.payment.label}

Vad händer nu?
Du får fraktinstruktioner och skickar mobilen när du är redo. {order.dealer_name} kontrollerar mobilen och betalar ut enligt valt betalningssätt.

Hälsningar,
Televera
"""


def _build_confirmation_email(order: OrderOut) -> EmailMessage:
    from_email = settings.smtp_from_email or settings.order_email_from
    from_name = settings.smtp_from_name or "Televera"

    message = EmailMessage()
    message["From"] = formataddr((from_name, from_email))
    message["To"] = str(order.customer.email)
    if settings.order_admin_email:
        message["Bcc"] = settings.order_admin_email
    if settings.smtp_reply_to:
        message["Reply-To"] = settings.smtp_reply_to
    message["Subject"] = f"Bekräftelse på din Televera-order {order.order_id}"
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


def _resend_api_key() -> str:
    if settings.resend_api_key:
        return settings.resend_api_key
    if settings.smtp_host == "smtp.resend.com":
        return settings.smtp_password
    return ""


async def _send_confirmation_email_resend(order: OrderOut) -> None:
    from_email = settings.smtp_from_email or settings.order_email_from
    from_name = settings.smtp_from_name or "Televera"
    payload: dict[str, Any] = {
        "from": formataddr((from_name, from_email)),
        "to": [str(order.customer.email)],
        "subject": f"Bekräftelse på din Televera-order {order.order_id}",
        "text": _confirmation_text(order),
        "html": _confirmation_html(order),
    }
    if settings.order_admin_email:
        payload["bcc"] = [settings.order_admin_email]
    if settings.smtp_reply_to:
        payload["reply_to"] = settings.smtp_reply_to

    async with httpx.AsyncClient(timeout=settings.order_submission_timeout_seconds) as client:
        response = await client.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {_resend_api_key()}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()


async def _send_confirmation_email(order: OrderOut) -> IntegrationStatus:
    from_email = settings.smtp_from_email or settings.order_email_from
    resend_api_key = _resend_api_key()
    smtp_configured = bool(settings.smtp_host and settings.smtp_username and settings.smtp_password and from_email)
    resend_configured = bool(resend_api_key and from_email)
    if not smtp_configured and not resend_configured:
        return IntegrationStatus(configured=False, ok=True, message="Mail saknar Resend API key eller SMTP-inställningar; hoppade över.")

    try:
        if resend_configured:
            await _send_confirmation_email_resend(order)
            return IntegrationStatus(configured=True, ok=True, message="Bekräftelsemail skickat via Resend API.")

        await to_thread(_send_confirmation_email_sync, order)
        return IntegrationStatus(configured=True, ok=True, message="Bekräftelsemail skickat via SMTP.")
    except Exception as exc:
        logger.exception("Kunde inte skicka ordermail för %s", order.order_id)
        return IntegrationStatus(configured=True, ok=False, message=str(exc))


def _confirmation_email_is_configured() -> bool:
    from_email = settings.smtp_from_email or settings.order_email_from
    return bool((_resend_api_key() and from_email) or (settings.smtp_host and settings.smtp_username and settings.smtp_password and from_email))


@router.post("/orders", response_model=OrderCreateResponse)
async def create_order(payload: OrderCreate):
    order = _make_order(payload)

    async def _send_order_integrations() -> None:
        try:
            sheets_status, email_status = await gather(
                _send_to_google_sheet(order),
                _send_confirmation_email(order),
            )
            if not sheets_status.ok:
                logger.warning("Order %s registrerad men Google Sheets misslyckades: %s", order.order_id, sheets_status.message)
            if not email_status.ok:
                logger.warning("Order %s registrerad men bekräftelsemail misslyckades: %s", order.order_id, email_status.message)
        except Exception:
            logger.exception("Order %s registrerad men integrationsjobbet kraschade", order.order_id)

    create_task(_send_order_integrations())

    sheets_status = IntegrationStatus(
        configured=_google_sheet_is_configured(),
        ok=True,
        message="Ordern är registrerad. Google Sheets körs i bakgrunden.",
    )
    email_status = IntegrationStatus(
        configured=_confirmation_email_is_configured(),
        ok=True,
        message="Ordern är registrerad. Bekräftelsemail körs i bakgrunden.",
    )

    return OrderCreateResponse(
        order=order,
        integrations={
            "google_sheets": sheets_status,
            "email": email_status,
        },
    )
