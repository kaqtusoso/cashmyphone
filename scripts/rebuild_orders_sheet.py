#!/usr/bin/env python3
"""
Rebuilds the Televera Orders worksheet with readable Swedish headers and
formatting. It preserves existing rows, but replaces the worksheet itself, just
like the Kostschema updater pattern.

Usage:
  python scripts/rebuild_orders_sheet.py \
    --credentials /path/to/credentials.json \
    --spreadsheet-id 1qAk0MTHvJ2Y3VUHu8LwEQibuClSOjN6-IKo-YvAFm2w
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from typing import Any

try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    print("Missing dependencies. Install with: pip install gspread google-auth")
    sys.exit(1)


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

WORKSHEET_NAME = "Orders"

COLUMNS = [
    ("order_id", "Ordernummer", 190),
    ("created_at", "Datum", 170),
    ("dealer", "Köpare", 130),
    ("model", "Modell", 180),
    ("storage", "Lagring", 95),
    ("price_sek", "Pris (SEK)", 105),
    ("bid_difference_sek", "Differens (SEK)", 125),
    ("shipping", "Frakt", 190),
    ("payment", "Betalning", 120),
    ("first_name", "Förnamn", 120),
    ("last_name", "Efternamn", 135),
    ("personal_number", "Personnummer", 150),
    ("email", "E-post", 230),
    ("phone", "Telefon", 145),
    ("address", "Adress", 185),
    ("postal_code", "Postnummer", 115),
    ("city", "Ort", 130),
    ("payment_details", "Betalningsuppgifter", 230),
    ("condition_answers", "Skick / frågesvar", 420),
]

OLD_TO_KEY = {key: key for key, _, _ in COLUMNS}
OLD_TO_KEY.update({header: key for key, header, _ in COLUMNS})

COLOR_HEADER = {"red": 0.0, "green": 0.45, "blue": 0.31}
COLOR_HEADER_TEXT = {"red": 1.0, "green": 1.0, "blue": 1.0}
COLOR_ROW = {"red": 0.97, "green": 0.99, "blue": 0.98}
COLOR_WHITE = {"red": 1.0, "green": 1.0, "blue": 1.0}
COLOR_TEXT = {"red": 0.08, "green": 0.1, "blue": 0.15}
FONT_FAMILY = "Arial"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--credentials", default=os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json"))
    parser.add_argument("--spreadsheet-id", default=os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID"))
    parser.add_argument("--worksheet", default=os.getenv("GOOGLE_SHEETS_WORKSHEET_NAME", WORKSHEET_NAME))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not args.spreadsheet_id:
        parser.error("--spreadsheet-id or GOOGLE_SHEETS_SPREADSHEET_ID is required")
    return args


def connect(credentials_file: str):
    service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    if service_account_json:
        info = json.loads(service_account_json.strip("'\""))
        private_key = info.get("private_key")
        if isinstance(private_key, str) and "\\n" in private_key:
            info["private_key"] = private_key.replace("\\n", "\n")
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    else:
        creds = Credentials.from_service_account_file(credentials_file, scopes=SCOPES)
    return gspread.authorize(creds)


def safe_json(value: str) -> Any:
    if not value:
        return None
    try:
        return json.loads(value)
    except Exception:
        return None


def format_payment_details(value: Any) -> str:
    if isinstance(value, str):
        parsed = safe_json(value)
        if not isinstance(parsed, dict):
            return value
        value = parsed

    if not isinstance(value, dict):
        return ""

    if value.get("swish_number"):
        return f"Swish: {value['swish_number']}"

    rows = []
    if value.get("clearing_number"):
        rows.append(f"Clearing: {value['clearing_number']}")
    if value.get("account_number"):
        rows.append(f"Konto: {value['account_number']}")
    if value.get("iban_number"):
        rows.append(f"IBAN: {value['iban_number']}")
    return "\n".join(rows)


def format_condition_answers(value: Any) -> str:
    if isinstance(value, str):
        parsed = safe_json(value)
        if not isinstance(parsed, dict):
            return value
        value = parsed

    if not isinstance(value, dict):
        return ""

    value_labels = {
        "chipped": "Sprickor/flisor",
        "scratched": "Repor",
        "none": "Inga skador",
        "visible": "Tydligt slitage",
        "some": "Visst slitage",
        "minimal": "Minimalt slitage",
        "cracked": "Sprucken",
    }
    rows = []
    if value.get("batteryHealth") is not None:
        rows.append(f"Batterihälsa: {value['batteryHealth']}%")
    for key, label in (
        ("screenGlass", "Skärmglas"),
        ("screenWear", "Skärmskick"),
        ("sidesWear", "Sidor"),
        ("backWear", "Baksida"),
    ):
        if value.get(key) is not None:
            rows.append(f"{label}: {value_labels.get(str(value[key]), value[key])}")

    functional_labels = {
        "powersOn": "Startar normalt",
        "network": "Nätverk fungerar",
        "faceId": "Face ID fungerar",
        "selfieCamera": "Selfiekamera fungerar",
        "speaker": "Högtalare fungerar",
        "bentOrWaterDamaged": "Böjd/vattenskadad",
    }
    functional = value.get("functional")
    if isinstance(functional, dict):
        for key, label in functional_labels.items():
            if functional.get(key) is not None:
                rows.append(f"{label}: {'Ja' if functional[key] else 'Nej'}")

    screen_function = value.get("screenFunction")
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


def normalize_created_at(value: str) -> str:
    if not value:
        return ""
    normalized = value.replace("Z", "+00:00")
    try:
        return dt.datetime.fromisoformat(normalized).strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return value


def normalize_row(raw: dict[str, Any]) -> list[Any]:
    normalized: dict[str, Any] = {}
    for source_header, value in raw.items():
        key = OLD_TO_KEY.get(source_header)
        if key:
            normalized[key] = value

    normalized["created_at"] = normalize_created_at(str(normalized.get("created_at", "")))
    normalized["payment_details"] = format_payment_details(normalized.get("payment_details"))
    normalized["condition_answers"] = format_condition_answers(normalized.get("condition_answers"))

    values = []
    for key, _, _ in COLUMNS:
        value = normalized.get(key, "")
        if key in {"price_sek", "bid_difference_sek"} and isinstance(value, str) and value.isdigit():
            value = int(value)
        values.append(value)
    return values


def read_existing_rows(spreadsheet, worksheet_name: str) -> list[list[Any]]:
    try:
        worksheet = spreadsheet.worksheet(worksheet_name)
    except gspread.WorksheetNotFound:
        return [[header for _, header, _ in COLUMNS]]

    values = worksheet.get_all_values()
    if len(values) <= 1:
        return [[header for _, header, _ in COLUMNS]]

    source_headers = values[0]
    rows = []
    for row in values[1:]:
        if not any(cell.strip() for cell in row):
            continue
        raw = {source_headers[index]: row[index] if index < len(row) else "" for index in range(len(source_headers))}
        rows.append(normalize_row(raw))

    return [[header for _, header, _ in COLUMNS], *rows]


def recreate_worksheet(spreadsheet, worksheet_name: str, rows: list[list[Any]]):
    temp_title = f"{worksheet_name}_new"
    try:
        temp = spreadsheet.worksheet(temp_title)
        spreadsheet.del_worksheet(temp)
    except gspread.WorksheetNotFound:
        pass

    worksheet = spreadsheet.add_worksheet(
        title=temp_title,
        rows=max(len(rows) + 20, 50),
        cols=len(COLUMNS),
    )
    worksheet.update(rows, value_input_option="USER_ENTERED")

    try:
        old = spreadsheet.worksheet(worksheet_name)
        spreadsheet.del_worksheet(old)
    except gspread.WorksheetNotFound:
        pass

    worksheet.update_title(worksheet_name)
    return worksheet


def row_format(sheet_id: int, row_idx: int, bg=None, bold=False, fg=None):
    fmt: dict[str, Any] = {
        "verticalAlignment": "MIDDLE",
        "wrapStrategy": "WRAP" if row_idx == 0 else "CLIP",
        "textFormat": {
            "fontFamily": FONT_FAMILY,
            "bold": bold,
            "foregroundColor": fg or COLOR_TEXT,
            "fontSize": 10 if row_idx else 11,
        },
    }
    if bg:
        fmt["backgroundColor"] = bg
    if bold:
        fmt["textFormat"]["bold"] = True
    return {
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": row_idx,
                "endRowIndex": row_idx + 1,
                "startColumnIndex": 0,
                "endColumnIndex": len(COLUMNS),
            },
            "cell": {"userEnteredFormat": fmt},
            "fields": "userEnteredFormat(backgroundColor,textFormat,verticalAlignment,wrapStrategy)",
        }
    }


def apply_formatting(worksheet, row_count: int):
    sheet_id = worksheet.id
    requests: list[dict[str, Any]] = [
        {
            "updateSheetProperties": {
                "properties": {
                    "sheetId": sheet_id,
                    "gridProperties": {"frozenRowCount": 1, "hideGridlines": True},
                },
                "fields": "gridProperties(frozenRowCount,hideGridlines)",
            }
        },
        row_format(sheet_id, 0, bg=COLOR_HEADER, bold=True, fg=COLOR_HEADER_TEXT),
        {
            "setBasicFilter": {
                "filter": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 0,
                        "startColumnIndex": 0,
                        "endColumnIndex": len(COLUMNS),
                    }
                }
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
    ]

    for index, (_, _, width) in enumerate(COLUMNS):
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

    for row_idx in range(1, row_count):
        requests.append(row_format(sheet_id, row_idx, bg=COLOR_WHITE))

    for money_key in ("price_sek", "bid_difference_sek"):
        money_col = next(index for index, (key, _, _) in enumerate(COLUMNS) if key == money_key)
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

    worksheet.spreadsheet.batch_update({"requests": requests})


def main() -> None:
    args = parse_args()
    client = connect(args.credentials)
    try:
        spreadsheet = client.open_by_key(args.spreadsheet_id)
    except PermissionError:
        print("No access to spreadsheet.")
        print("Share the Google Sheet with the service account as Editor, then run this again.")
        if os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"):
            print("Credentials source: GOOGLE_SERVICE_ACCOUNT_JSON")
        else:
            print(f"Credentials file: {args.credentials}")
        sys.exit(1)

    rows = read_existing_rows(spreadsheet, args.worksheet)

    print(f"Rows to write: {len(rows) - 1} orders")
    if args.dry_run:
        for row in rows[:3]:
            print(row)
        return

    worksheet = recreate_worksheet(spreadsheet, args.worksheet, rows)
    apply_formatting(worksheet, len(rows))
    print(f"Rebuilt worksheet '{args.worksheet}' in https://docs.google.com/spreadsheets/d/{spreadsheet.id}")


if __name__ == "__main__":
    main()
