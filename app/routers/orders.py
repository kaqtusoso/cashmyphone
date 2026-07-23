import json
import logging
import smtplib
from asyncio import create_task, gather, to_thread
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import formataddr
from hashlib import sha256
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
    ("bid_difference_sek", "Differens (SEK)", 125),
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
    ("feedback_email_sent_at", "Feedbackmail skickat", 175),
    ("feedback_email_status", "Feedbackmail status", 145),
    ("feedback_email_error", "Feedbackmail fel", 260),
    ("feedback_email_id", "Resend mejl-ID", 245),
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
    color: str | None = None
    dealer_id: str = Field(min_length=1)
    dealer_name: str = Field(min_length=1)
    price_sek: int = Field(ge=0)
    bid_difference_sek: int | None = Field(default=None, ge=0)
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


def _format_condition_answers(condition_answers: dict[str, Any] | None, color: str | None = None) -> str:
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
    if not condition_answers:
        if color:
            rows.append(f"Färg: {color}")
        return "\n".join(rows)

    battery_health = condition_answers.get("batteryHealth")
    if battery_health is not None:
        rows.append(f"{labels['batteryHealth']}: {battery_health}%")
    if color:
        rows.append(f"Färg: {color}")

    for key in ("screenGlass", "screenWear", "sidesWear", "backWear"):
        value = condition_answers.get(key)
        if value is None:
            continue
        formatted_value = value_labels.get(str(value), str(value))
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
        "bid_difference_sek": order.bid_difference_sek,
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
        "condition_answers": _format_condition_answers(order.condition_answers, order.color),
        "feedback_email_sent_at": "",
        "feedback_email_status": "",
        "feedback_email_error": "",
        "feedback_email_id": "",
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


def _sheet_column_letter(index: int) -> str:
    letters = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        letters = chr(65 + remainder) + letters
    return letters


def _sheet_values_range(sheet_name: str) -> str:
    last_column = _sheet_column_letter(len(SHEET_COLUMNS))
    return httpx.URL(f"https://example.com/{sheet_name}!A:{last_column}").raw_path.decode().lstrip("/")


def _sheet_column_index(key: str) -> int:
    return next(index for index, (column_key, _, _) in enumerate(SHEET_COLUMNS) if column_key == key)


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

    for money_key in ("price_sek", "bid_difference_sek"):
        money_col = _sheet_column_index(money_key)
        requests.append(
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 1,
                        "startColumnIndex": money_col,
                        "endColumnIndex": money_col + 1,
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "numberFormat": {"type": "NUMBER", "pattern": '#,##0 "kr"'},
                            "horizontalAlignment": "RIGHT",
                        }
                    },
                    "fields": "userEnteredFormat(numberFormat,horizontalAlignment)",
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

    if existing_values and existing_values[0] != SHEET_HEADERS:
        existing_headers = existing_values[0]
        if existing_headers == SHEET_HEADERS[: len(existing_headers)]:
            update_response = await client.put(
                f"{base_url}/{encoded_range}",
                params={"valueInputOption": "RAW"},
                headers=headers,
                json={"values": [SHEET_HEADERS]},
            )
            update_response.raise_for_status()
        else:
            await _rebuild_google_sheet(client, token)
            return

    if not existing_values:
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
    encoded_range = _sheet_values_range(sheet_name)
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
        encoded_range = _sheet_values_range(sheet_name)

        async with httpx.AsyncClient(timeout=settings.order_submission_timeout_seconds) as client:
            await _ensure_google_sheet_layout(client, token)
            sheet_id = await _get_google_sheet_id(client, token)
            response = await client.post(
                f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{encoded_range}:append",
                params={"valueInputOption": "USER_ENTERED", "insertDataOption": "OVERWRITE"},
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
                            *[
                                {
                                    "repeatCell": {
                                        "range": {
                                            "sheetId": sheet_id,
                                            "startRowIndex": updated_end_row - 1,
                                            "endRowIndex": updated_end_row,
                                            "startColumnIndex": _sheet_column_index(money_key),
                                            "endColumnIndex": _sheet_column_index(money_key) + 1,
                                        },
                                        "cell": {
                                            "userEnteredFormat": {
                                                "numberFormat": {"type": "NUMBER", "pattern": '#,##0 "kr"'},
                                                "horizontalAlignment": "RIGHT",
                                            }
                                        },
                                        "fields": "userEnteredFormat(numberFormat,horizontalAlignment)",
                                    }
                                }
                                for money_key in ("price_sek", "bid_difference_sek")
                            ],
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


def _confirmation_steps(order: OrderOut) -> list[tuple[str, str]]:
    dealer_name = order.dealer_name
    payment_label = order.payment.label
    shipping_option = order.shipping_option.strip().lower()

    payment_text = (
        f"{dealer_name} kontrollerar mobilen och betalar via {payment_label} "
        "efter godkänd kontroll."
    )

    if shipping_option == "sales-package":
        return [
            ("Invänta paket", f"{dealer_name} skickar försäljningspaketet till din adress."),
            ("Packa & skicka", "Förbered mobilen och följ instruktionerna i paketet."),
            ("Betalning", payment_text),
        ]

    if shipping_option == "email-label":
        return [
            ("Invänta frakt", f"{dealer_name} skickar digitala fraktinstruktioner till dig."),
            ("Packa & lämna", "Följ instruktionerna och lämna paketet hos angivet ombud."),
            ("Betalning", payment_text),
        ]

    if shipping_option == "store-dropoff":
        _, separator, selected_store = order.shipping_label.partition(":")
        destination = selected_store.strip() if separator else order.shipping_label
        return [
            ("Lämna i butik", f"Ta med den förberedda mobilen till {destination}."),
            ("Kontroll", f"{dealer_name} kontrollerar mobilen i butik."),
            ("Betalning", f"Utbetalning sker via {payment_label} efter godkänd kontroll."),
        ]

    return [
        ("Följ instruktionerna", f"Följ fraktinstruktionerna från {dealer_name}."),
        ("Kontroll", f"{dealer_name} kontrollerar mobilen när den har kommit fram."),
        ("Betalning", f"Utbetalning sker via {payment_label} efter godkänd kontroll."),
    ]


def _confirmation_timeline_markup(steps: list[tuple[str, str]]) -> str:
    rows: list[str] = []
    for index, (title, description) in enumerate(steps, start=1):
        if index == 1:
            circle_style = "background:#15bd80;color:#ffffff;border:2px solid #15bd80;"
        else:
            circle_style = "background:#ffffff;color:#15bd80;border:2px solid #c0e6d2;"

        connector = (
            '<div style="width:2px;height:54px;background:#dfe6df;margin:0 auto;font-size:0;line-height:0;">&nbsp;</div>'
            if index < len(steps)
            else ""
        )
        text_padding = "2px 0 18px 14px" if index < len(steps) else "2px 0 0 14px"
        rows.append(
            f"""
                            <tr>
                              <td width="44" align="center" valign="top" style="width:44px;vertical-align:top;">
                                <div style="width:38px;height:38px;border-radius:19px;box-sizing:border-box;{circle_style}text-align:center;line-height:34px;font-size:14px;font-weight:700;mso-line-height-rule:exactly;">{index}</div>
                                {connector}
                              </td>
                              <td valign="top" style="vertical-align:top;padding:{text_padding};">
                                <div style="font-size:15px;line-height:20px;color:#2f322c;font-weight:700;">{escape(title)}</div>
                                <div class="tv-step-sub" style="margin-top:5px;font-size:13px;line-height:19px;color:#8b918a;">{escape(description)}</div>
                              </td>
                            </tr>"""
        )

    return f"""
                          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="margin-top:18px;">
{''.join(rows)}
                          </table>"""


def _confirmation_shipping_label_html(order: OrderOut) -> str:
    if order.shipping_option.strip().lower() == "store-dropoff":
        label_prefix, separator, selected_store = order.shipping_label.partition(":")
        if separator and selected_store.strip():
            return (
                f"{escape(label_prefix)}:<br>"
                f'<span style="display:inline-block;margin-top:3px;">{escape(selected_store.strip())}</span>'
            )
    return escape(order.shipping_label)


def _confirmation_html(order: OrderOut) -> str:
    price = f"{order.price_sek:,}".replace(",", " ")
    customer_name = escape(order.customer.first_name)
    order_id = escape(order.order_id)
    model = escape(order.model)
    storage = escape(order.storage)
    dealer_name = escape(order.dealer_name)
    shipping_label = _confirmation_shipping_label_html(order)
    payment_label = escape(order.payment.label)
    phone_model = f"{model} {storage}"
    logo_url = f"{settings.public_base_url.rstrip('/')}/mail-assets/televera-logo-full.png"
    timeline_markup = _confirmation_timeline_markup(_confirmation_steps(order))

    return f"""
    <!doctype html>
    <html lang="sv">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta name="x-apple-disable-message-reformatting">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <meta name="color-scheme" content="light dark">
        <meta name="supported-color-schemes" content="light dark">
        <title>Televera - Orderbekräftelse</title>
        <style>
          @media only screen and (max-width: 600px) {{
            .tv-px {{ padding-left: 20px !important; padding-right: 20px !important; }}
            .tv-h1 {{ font-size: 24px !important; line-height: 30px !important; }}
            .tv-price {{ font-size: 26px !important; }}
            .tv-step-sub {{ font-size: 12px !important; }}
          }}
        </style>
      </head>
      <body style="margin:0;padding:0;background:#edf0ea;color:#2f322c;font-family:'Helvetica Neue',Arial,Helvetica,sans-serif;-webkit-font-smoothing:antialiased;">
        <div style="display:none;max-height:0;overflow:hidden;opacity:0;color:#edf0ea;font-size:1px;line-height:1px;">
          Tack {customer_name}, vi har tagit emot din order {order_id}. Uppskattat pris {price} kr.
        </div>

        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background:#edf0ea;margin:0;padding:30px 12px;">
          <tr>
            <td align="center">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="max-width:600px;background:#ffffff;border-radius:18px;overflow:hidden;border:1px solid #cfd4cb;box-shadow:0 8px 26px rgba(35,45,38,0.06);">
                <tr>
                  <td class="tv-px" align="center" style="background:#05B87A;padding:24px 30px;text-align:center;">
                    <img src="{logo_url}" width="150" alt="Televera" style="display:block;width:150px;max-width:150px;height:auto;margin:0 auto;border:0;outline:none;text-decoration:none;color:#ffffff;font-size:24px;font-weight:800;font-family:'Helvetica Neue',Arial,Helvetica,sans-serif;">
                  </td>
                </tr>

                <tr>
                  <td class="tv-px" style="padding:28px 30px 8px;">
                    <h1 class="tv-h1" style="margin:0;font-size:26px;line-height:31px;color:#2f322c;font-weight:700;letter-spacing:-0.02em;">Tack {customer_name}, vi har tagit emot din order.</h1>
                    <p style="margin:14px 0 0;color:#8b918a;font-size:15px;line-height:24px;">Vi har registrerat att du vill sälja din <strong style="color:#2f322c;font-weight:600;">{phone_model}</strong>. Spara ordernumret nedan om du behöver kontakta oss.</p>
                  </td>
                </tr>

                <tr>
                  <td class="tv-px" style="padding:18px 30px 6px;">
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background:#e7f6ee;border:1px solid #c0e6d2;border-radius:14px;overflow:hidden;">
                      <tr>
                        <td style="padding:18px 20px 16px;vertical-align:top;">
                          <div style="font-size:11px;text-transform:uppercase;letter-spacing:0.1em;color:#5c7d6b;font-family:'Courier New',Courier,monospace;">Ordernummer</div>
                          <div style="margin-top:7px;font-size:20px;line-height:24px;color:#0b5538;font-weight:700;font-family:'Courier New',Courier,monospace;letter-spacing:-0.01em;">{order_id}</div>
                        </td>
                      </tr>
                      <tr>
                        <td style="padding:0 20px;">
                          <div style="height:1px;background:#c0e6d2;font-size:0;line-height:0;">&nbsp;</div>
                        </td>
                      </tr>
                      <tr>
                        <td style="padding:16px 20px 18px;vertical-align:top;text-align:left;">
                          <div style="font-size:11px;text-transform:uppercase;letter-spacing:0.1em;color:#5c7d6b;font-family:'Courier New',Courier,monospace;">Uppskattat pris</div>
                          <div class="tv-price" style="margin-top:5px;font-size:28px;line-height:32px;color:#15bd80;font-weight:800;letter-spacing:-0.02em;">{price} kr</div>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>

                <tr>
                  <td class="tv-px" style="padding:14px 30px 4px;">
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="border-collapse:collapse;">
                      <tr>
                        <td style="padding:12px 0;border-bottom:1px solid #e7eae3;color:#8b918a;font-size:14px;">Mobil</td>
                        <td align="right" style="padding:12px 0;border-bottom:1px solid #e7eae3;color:#2f322c;font-size:14px;font-weight:600;">{phone_model}</td>
                      </tr>
                      <tr>
                        <td style="padding:12px 0;border-bottom:1px solid #e7eae3;color:#8b918a;font-size:14px;">Köpare</td>
                        <td align="right" style="padding:12px 0;border-bottom:1px solid #e7eae3;color:#2f322c;font-size:14px;font-weight:600;">{dealer_name}</td>
                      </tr>
                      <tr>
                        <td style="padding:12px 0;border-bottom:1px solid #e7eae3;color:#8b918a;font-size:14px;">Frakt</td>
                        <td align="right" style="padding:12px 0;border-bottom:1px solid #e7eae3;color:#2f322c;font-size:14px;font-weight:600;">{shipping_label}</td>
                      </tr>
                      <tr>
                        <td style="padding:12px 0;color:#8b918a;font-size:14px;">Betalning</td>
                        <td align="right" style="padding:12px 0;color:#2f322c;font-size:14px;font-weight:600;">{payment_label}</td>
                      </tr>
                    </table>
                  </td>
                </tr>

                <tr>
                  <td class="tv-px" style="padding:16px 30px 4px;">
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background:#fff8e6;border:1px solid #f0d58c;border-radius:14px;">
                      <tr>
                        <td style="padding:18px 18px 19px;">
                          <div style="font-size:17px;line-height:22px;color:#2f322c;font-weight:700;">Viktigt innan du skickar eller lämnar in mobilen</div>
                          <div style="margin-top:10px;font-size:14px;line-height:21px;color:#64685f;">
                            Säkerhetskopiera det du vill behålla. <strong style="color:#2f322c;">Stäng av Hitta min iPhone</strong>, logga ut från Apple-ID och fabriksåterställ mobilen. Ta även ur eventuellt fysiskt SIM-kort.
                          </div>
                          <div style="margin-top:9px;font-size:13px;line-height:20px;color:#8a6420;font-weight:600;">
                            Hitta min iPhone måste vara avstängt när köparen tar emot mobilen.
                          </div>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>

                <tr>
                  <td class="tv-px" style="padding:16px 30px 30px;">
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background:#f1f3f2;border:1px solid #d9dedb;border-radius:14px;">
                      <tr>
                        <td style="padding:18px 18px 22px;">
                          <div style="font-size:17px;line-height:22px;color:#2f322c;font-weight:700;">Vad händer nu?</div>
{timeline_markup}
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>

                <tr>
                  <td class="tv-px" style="padding:0 30px 30px;color:#8b918a;font-size:14px;line-height:22px;">
                    Hälsningar,<br>
                    <strong style="color:#2f322c;font-weight:600;">Televera</strong>
                  </td>
                </tr>
              </table>
              <div style="max-width:600px;margin:14px auto 0;color:#aeb4ac;font-size:12px;line-height:18px;text-align:center;font-family:'Courier New',Courier,monospace;letter-spacing:0.03em;">
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
    steps = _confirmation_steps(order)
    step_text = "\n".join(
        f"{index}. {title}: {description}"
        for index, (title, description) in enumerate(steps, start=1)
    )
    return f"""Hej {order.customer.first_name},

Tack för din order hos Televera.

Ordernummer: {order.order_id}
Mobil: {order.model} {order.storage}
Köpare: {order.dealer_name}
Uppskattat pris: {price} kr
Frakt: {order.shipping_label}
Betalning: {order.payment.label}

Viktigt innan du skickar eller lämnar in mobilen
Säkerhetskopiera det du vill behålla. Stäng av Hitta min iPhone, logga ut från Apple-ID och fabriksåterställ mobilen. Ta även ur eventuellt fysiskt SIM-kort.
Hitta min iPhone måste vara avstängt när köparen tar emot mobilen.

Vad händer nu?
{step_text}

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


def _require_order_admin_key(x_api_key: str | None) -> None:
    if not settings.scrape_api_key or x_api_key != settings.scrape_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


def _feedback_row_value(row: dict[str, Any], key: str) -> str:
    return str(row.get(key) or "").strip()


def _parse_feedback_order_datetime(value: str) -> datetime | None:
    value = value.strip()
    if not value:
        return None

    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            pass

    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _feedback_email_subject(row: dict[str, Any]) -> str:
    order_id = _feedback_row_value(row, "order_id")
    return f"Hur gick det med Televera?{f' ({order_id})' if order_id else ''}"


def _feedback_email_idempotency_key(row: dict[str, Any]) -> str:
    identity = "|".join(
        (
            _feedback_row_value(row, "order_id"),
            _feedback_row_value(row, "email").lower(),
            _feedback_row_value(row, "created_at"),
        )
    )
    digest = sha256(identity.encode("utf-8")).hexdigest()[:32]
    return f"televera-feedback/{digest}"


def _feedback_email_text(row: dict[str, Any]) -> str:
    first_name = _feedback_row_value(row, "first_name") or "där"
    model = _feedback_row_value(row, "model")
    order_id = _feedback_row_value(row, "order_id")
    trustpilot_url = settings.trustpilot_review_url.strip()
    order_line = f"\nOrdernummer: {order_id}" if order_id else ""
    model_line = f"\nMobil: {model}" if model else ""

    return f"""Hej {first_name},

Nu har det gått ett par veckor sedan din beställning via Televera.

Lämna gärna ett snabbt betyg. Din feedback hjälper oss att bli bättre:

{trustpilot_url}
{order_line}{model_line}

Tack för att du hjälper oss att göra Televera bättre.

Hälsningar,
Televera
"""


def _feedback_rating_url(stars: int) -> str:
    base_url = settings.trustpilot_review_url.strip()
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}stars={stars}"


def _feedback_email_html(row: dict[str, Any]) -> str:
    first_name_raw = _feedback_row_value(row, "first_name")
    first_name = escape(first_name_raw)
    model = escape(_feedback_row_value(row, "model"))
    order_id = escape(_feedback_row_value(row, "order_id"))
    logo_url = escape(
        f"{settings.public_base_url.rstrip('/')}/mail-assets/televera-logo-full.png",
        quote=True,
    )
    heading = f"Vad tyckte du, {first_name}?" if first_name else "Vad tyckte du?"
    details = []
    if order_id:
        details.append(
            f'Ordernummer: <span style="color:#5b6b63;">{order_id}</span>'
        )
    if model:
        details.append(f'Mobil: <span style="color:#5b6b63;">{model}</span>')
    details_html = "".join(f"<div>{detail}</div>" for detail in details)
    stars_html = "".join(
        f"""
                      <td class="tv-star-cell" align="center" style="padding:0 5px;">
                        <a class="tv-star" href="{escape(_feedback_rating_url(stars), quote=True)}" target="_blank" rel="noopener" title="{stars} av 5" aria-label="{stars} av 5 stjärnor" style="display:inline-block;width:50px;height:50px;line-height:50px;border-radius:50%;border:2px solid #dfe6e2;background:#f6f9f7;color:#c4cec8;text-align:center;text-decoration:none;font-family:Arial,Helvetica,sans-serif;font-size:26px;font-weight:700;">★</a>
                      </td>"""
        for stars in range(1, 6)
    )

    return f"""<!doctype html>
<html lang="sv">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="x-apple-disable-message-reformatting">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>Hur gick det med Televera?</title>
    <style>
      .tv-star:hover {{
        border-color:#12b57a !important;
        background:#12b57a !important;
        color:#ffffff !important;
      }}
      @media only screen and (max-width:600px) {{
        .tv-shell {{ padding:24px 10px 0 !important; }}
        .tv-bottom-space {{ height:24px !important;line-height:24px !important; }}
        .tv-content {{ padding-left:22px !important;padding-right:22px !important; }}
        .tv-heading {{ font-size:28px !important;line-height:32px !important; }}
        .tv-star {{ width:42px !important;height:42px !important;line-height:42px !important;font-size:23px !important; }}
        .tv-star-cell {{ padding-left:3px !important;padding-right:3px !important; }}
      }}
    </style>
  </head>
  <body style="margin:0;padding:0;background:#eef1ef;color:#16241d;font-family:'Nunito Sans','Helvetica Neue',Arial,Helvetica,sans-serif;-webkit-font-smoothing:antialiased;">
    <div style="display:none;max-height:0;overflow:hidden;opacity:0;color:#eef1ef;font-size:1px;line-height:1px;">
      Sätt ett betyg på din upplevelse med Televera – det tar bara några sekunder.
    </div>
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:100%;background:#eef1ef;margin:0;">
      <tr>
        <td class="tv-shell" align="center" style="padding:48px 20px 0;">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:100%;max-width:560px;background:transparent;box-shadow:0 12px 40px rgba(16,90,60,0.12);">
            <tr>
              <td align="center" style="background:#12b57a;padding:26px 34px;border-radius:20px 20px 0 0;">
                <img src="{logo_url}" width="150" alt="Televera" style="display:block;width:150px;max-width:150px;height:auto;margin:0 auto;border:0;outline:none;text-decoration:none;color:#ffffff;font-size:24px;font-weight:800;">
              </td>
            </tr>
            <tr>
              <td class="tv-content" align="center" style="background:#ffffff;padding:40px 40px 34px;text-align:center;">
                <h1 class="tv-heading" style="margin:0;font-family:'Arial Rounded MT Bold','Trebuchet MS',Arial,sans-serif;font-weight:800;font-size:32px;line-height:35px;color:#16241d;">{heading}</h1>
                <p style="font-size:17px;line-height:26px;color:#5b6b63;margin:14px auto 0;max-width:400px;">Nu har det gått ett par veckor sedan din beställning via Televera. Lämna gärna ett snabbt betyg – din feedback hjälper oss att bli bättre.</p>

                <table role="presentation" cellspacing="0" cellpadding="0" border="0" align="center" style="margin:30px auto 0;">
                  <tr>
                    {stars_html}
                  </tr>
                </table>
              </td>
            </tr>
            <tr>
              <td class="tv-content" style="background:#ffffff;border-top:1px solid #eaefec;padding:22px 40px 30px;border-radius:0 0 20px 20px;">
                <div style="font-size:13px;line-height:22px;color:#8a988f;">
                {details_html}
                </div>
                <p style="font-size:13px;line-height:20px;color:#aab5ae;margin:16px 0 0;">Tack för att du hjälper oss att göra Televera bättre.</p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
      <tr>
        <td class="tv-bottom-space" height="48" style="height:48px;line-height:48px;font-size:1px;background:#eef1ef;">&nbsp;</td>
      </tr>
    </table>
  </body>
</html>"""


def _build_feedback_email(row: dict[str, Any]) -> EmailMessage:
    from_email = settings.smtp_from_email or settings.order_email_from
    from_name = settings.smtp_from_name or "Televera"

    message = EmailMessage()
    message["From"] = formataddr((from_name, from_email))
    message["To"] = _feedback_row_value(row, "email")
    if settings.smtp_reply_to:
        message["Reply-To"] = settings.smtp_reply_to
    message["Resend-Idempotency-Key"] = _feedback_email_idempotency_key(row)
    message["Subject"] = _feedback_email_subject(row)
    message.set_content(_feedback_email_text(row))
    message.add_alternative(_feedback_email_html(row), subtype="html")
    return message


def _send_feedback_email_sync(row: dict[str, Any]) -> None:
    message = _build_feedback_email(row)
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=settings.order_submission_timeout_seconds) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message)


async def _send_feedback_email_resend(row: dict[str, Any]) -> str:
    from_email = settings.smtp_from_email or settings.order_email_from
    from_name = settings.smtp_from_name or "Televera"
    payload: dict[str, Any] = {
        "from": formataddr((from_name, from_email)),
        "to": [_feedback_row_value(row, "email")],
        "subject": _feedback_email_subject(row),
        "text": _feedback_email_text(row),
        "html": _feedback_email_html(row),
    }
    if settings.smtp_reply_to:
        payload["reply_to"] = settings.smtp_reply_to

    async with httpx.AsyncClient(timeout=settings.order_submission_timeout_seconds) as client:
        response = await client.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {_resend_api_key()}",
                "Content-Type": "application/json",
                "Idempotency-Key": _feedback_email_idempotency_key(row),
            },
            json=payload,
        )
        response.raise_for_status()
        return str(response.json().get("id") or "")


def _feedback_email_is_configured() -> bool:
    from_email = settings.smtp_from_email or settings.order_email_from
    resend_configured = bool(_resend_api_key() and from_email)
    smtp_configured = bool(settings.smtp_host and settings.smtp_username and settings.smtp_password and from_email)
    return bool(
        settings.feedback_email_enabled
        and settings.feedback_email_start_date.strip()
        and settings.trustpilot_review_url.strip()
        and (resend_configured or smtp_configured)
    )


async def _send_feedback_email(row: dict[str, Any]) -> str:
    if _resend_api_key():
        return await _send_feedback_email_resend(row)
    await to_thread(_send_feedback_email_sync, row)
    return ""


def _feedback_candidate_is_due(row: dict[str, Any], now: datetime) -> bool:
    if _feedback_row_value(row, "feedback_email_sent_at"):
        return False
    if not _feedback_row_value(row, "email"):
        return False
    if _feedback_row_value(row, "feedback_email_status").lower() in {"sending", "sent", "scheduled"}:
        return False

    created_at = _parse_feedback_order_datetime(_feedback_row_value(row, "created_at"))
    start_at = _parse_feedback_order_datetime(settings.feedback_email_start_date)
    if not created_at or not start_at or created_at < start_at:
        return False

    return created_at <= now - timedelta(days=settings.feedback_email_delay_days)


async def _update_feedback_email_sheet_status(
    client: httpx.AsyncClient,
    base_url: str,
    headers: dict[str, str],
    sheet_name: str,
    sheet_row_number: int,
    values: list[Any],
) -> None:
    start_col = _sheet_column_letter(_sheet_column_index("feedback_email_sent_at") + 1)
    end_col = _sheet_column_letter(_sheet_column_index("feedback_email_id") + 1)
    update_range = httpx.URL(
        f"https://example.com/{sheet_name}!{start_col}{sheet_row_number}:{end_col}{sheet_row_number}"
    ).raw_path.decode().lstrip("/")
    response = await client.put(
        f"{base_url}/{update_range}",
        params={"valueInputOption": "USER_ENTERED"},
        headers=headers,
        json={"values": [values]},
    )
    response.raise_for_status()


async def run_order_feedback_emails(dry_run: bool = False) -> IntegrationStatus:
    if not _feedback_email_is_configured():
        return IntegrationStatus(
            configured=False,
            ok=True,
            message="Feedbackmail är inte aktiverat eller saknar startdatum, Trustpilot-länk eller mailinställningar.",
        )
    if not settings.google_service_account_json or not settings.google_sheets_spreadsheet_id:
        return IntegrationStatus(
            configured=False,
            ok=True,
            message="Feedbackmail kräver Google Sheets API med service account och spreadsheet ID.",
        )

    try:
        token = await _get_google_access_token()
        sheet_name = settings.google_sheets_worksheet_name
        spreadsheet_id = settings.google_sheets_spreadsheet_id
        encoded_range = _sheet_values_range(sheet_name)
        base_url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values"
        headers = {"Authorization": f"Bearer {token}"}
        sent_count = 0
        failed_count = 0
        now = datetime.now(timezone.utc)

        async with httpx.AsyncClient(timeout=settings.order_submission_timeout_seconds) as client:
            await _ensure_google_sheet_layout(client, token)

            get_response = await client.get(f"{base_url}/{encoded_range}", headers=headers)
            get_response.raise_for_status()
            values = get_response.json().get("values", [])
            if not values:
                return IntegrationStatus(configured=True, ok=True, message="Orderarket är tomt; inga feedbackmail skickades.")

            source_headers = values[0]
            rows: list[tuple[int, dict[str, Any]]] = []
            for sheet_row_number, raw_row in enumerate(values[1:], start=2):
                normalized = _normalize_existing_sheet_row(source_headers, raw_row)
                row = {key: normalized[index] if index < len(normalized) else "" for index, key in enumerate(SHEET_KEYS)}
                if _feedback_candidate_is_due(row, now):
                    rows.append((sheet_row_number, row))

            if dry_run:
                return IntegrationStatus(
                    configured=True,
                    ok=True,
                    message=f"Feedbackmail dry-run: {len(rows)} orderrader är redo för utskick.",
                )

            for sheet_row_number, row in rows[: settings.feedback_email_batch_size]:
                await _update_feedback_email_sheet_status(
                    client,
                    base_url,
                    headers,
                    sheet_name,
                    sheet_row_number,
                    ["", "sending", "", ""],
                )

                try:
                    email_id = await _send_feedback_email(row)
                    sent_count += 1
                    status_values = [now.strftime("%Y-%m-%d %H:%M"), "sent", "", email_id]
                except Exception as exc:
                    failed_count += 1
                    logger.exception("Kunde inte skicka feedbackmail för order %s", _feedback_row_value(row, "order_id"))
                    status_values = ["", "failed", str(exc)[:500], ""]

                await _update_feedback_email_sheet_status(
                    client,
                    base_url,
                    headers,
                    sheet_name,
                    sheet_row_number,
                    status_values,
                )

        ok = failed_count == 0
        return IntegrationStatus(
            configured=True,
            ok=ok,
            message=f"Feedbackmail: {sent_count} skickade, {failed_count} misslyckade.",
        )
    except Exception as exc:
        logger.exception("Feedbackmail-jobbet misslyckades")
        return IntegrationStatus(configured=True, ok=False, message=str(exc))


@router.post("/orders/feedback-emails/run", response_model=IntegrationStatus)
async def run_feedback_emails_now(
    dry_run: bool = False,
    x_api_key: str | None = Header(default=None),
):
    _require_order_admin_key(x_api_key)
    return await run_order_feedback_emails(dry_run=dry_run)


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
