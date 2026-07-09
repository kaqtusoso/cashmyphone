#!/usr/bin/env python3
"""
Scrape FixTech's Swedish storefront inventory/prices.

FixTech uses Hostinger/Zyro ecommerce. The public frontend calls Hostinger's
store API, which exposes product variants with prices and availability.

Outputs:
  data/retail_prices/fixtech_storefront_latest.json
  data/retail_prices/fixtech_storefront_latest.csv
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from curl_cffi.requests import AsyncSession


STORE_ID = "store_01J9K3NR317QFXRC11830V4QGK"
BASE_URL = "https://fixtech.se"
API_URL = f"https://api-ecommerce.hostinger.com/store/{STORE_ID}/products"
OUT_DIR = Path("data/retail_prices")

HEADERS = {
    "Accept": "application/json",
    "Accept-Language": "sv-SE,sv;q=0.9,en-US;q=0.8,en;q=0.7",
    "Origin": BASE_URL,
    "Referer": f"{BASE_URL}/",
    "User-Agent": "Mozilla/5.0",
}

LOGGER = logging.getLogger("fixtech-storefront")

ACCESSORY_RE = re.compile(
    r"\b(skal|mobilskal|fodral|skärmskydd|skarmskydd|tempered|glass|protector|privacy|magnet)\b",
    re.I,
)


async def _get_json(session: AsyncSession, url: str, params: dict[str, Any]) -> dict[str, Any]:
    response = await session.get(url, params=params, headers=HEADERS, timeout=45)
    response.raise_for_status()
    return response.json()


def _amount_to_sek(value: int | None) -> int | None:
    if value is None:
        return None
    return round(value / 100)


def _parse_storage_gb(text: str | None) -> int | None:
    if not text:
        return None
    match = re.search(r"(\d+)\s*(GB|TB)", text, re.I)
    if not match:
        return None
    amount = int(match.group(1))
    return amount * 1024 if match.group(2).lower() == "tb" else amount


def _clean_model(text: str) -> str:
    text = re.sub(r"\bApple\b", "", text, flags=re.I)
    text = re.sub(r"\b5G\s+smartphone\b", "", text, flags=re.I)
    text = re.sub(r"^.*?\|\s*", "", text)
    text = re.sub(r"\b\d+\s*(GB|TB)\b.*$", "", text, flags=re.I)
    text = re.sub(r"\s+", " ", text).strip(" ,-")
    return text.replace("Iphone", "iPhone")


def _parse_color(text: str | None) -> str | None:
    if not text:
        return None
    value = re.split(r"\d+\s*(?:GB|TB)", text, flags=re.I)[-1]
    value = value.replace("-NYHET", "").replace("NYHET", "")
    value = value.strip(" ,-()")
    return value.capitalize() if value else None


def _variant_price(variant: dict[str, Any]) -> tuple[int | None, int | None, str]:
    price = (variant.get("prices") or [{}])[0]
    sale = _amount_to_sek(price.get("sale_amount"))
    regular = _amount_to_sek(price.get("amount"))
    currency = (price.get("currency_code") or "sek").upper()
    return sale or regular, regular if sale and regular and regular != sale else None, currency


def parse_products(products: list[dict[str, Any]], include_all_phones: bool = False) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for product in products:
        title = product.get("title") or ""
        if ACCESSORY_RE.search(title):
            continue
        if include_all_phones:
            if not re.search(r"\b(iPhone|Samsung Galaxy)\b", title, re.I):
                continue
        elif not re.search(r"\biPhone\b", title, re.I):
            continue

        for variant in product.get("variants") or []:
            if not variant.get("is_available"):
                continue
            variant_title = variant.get("title") or title
            price_sek, reference_price_sek, currency = _variant_price(variant)
            if not price_sek:
                continue
            image_url = variant.get("image_url") or product.get("thumbnail")

            rows.append(
                {
                    "retailer": "fixtech",
                    "sku": variant.get("sku") or variant.get("id"),
                    "variant_id": variant.get("id"),
                    "product_id": product.get("id"),
                    "model": _clean_model(title),
                    "storage_gb": _parse_storage_gb(variant_title) or _parse_storage_gb(variant.get("sku")),
                    "storage": variant.get("sku"),
                    "color": _parse_color(variant_title),
                    "condition_grade": product.get("ribbon_text"),
                    "price_sek": price_sek,
                    "reference_price_sek": reference_price_sek,
                    "currency": currency,
                    "stock": 1,
                    "url": f"{BASE_URL}/{product.get('slug') or product.get('url_handle')}",
                    "image_url": image_url,
                }
            )
    return rows


async def scrape(include_all_phones: bool = False) -> list[dict[str, Any]]:
    async with AsyncSession(impersonate="chrome136") as session:
        first = await _get_json(session, API_URL, {"limit": 100, "offset": 0})
        products = list(first.get("products") or [])
        count = int(first.get("count") or len(products))
        LOGGER.info("FixTech API returned %s products", count)

        offset = len(products)
        while offset < count:
            data = await _get_json(session, API_URL, {"limit": 100, "offset": offset})
            batch = data.get("products") or []
            if not batch:
                break
            products.extend(batch)
            offset += len(batch)
            await asyncio.sleep(0.25)

    rows = parse_products(products, include_all_phones=include_all_phones)
    scraped_at = datetime.now(timezone.utc).isoformat()
    for row in rows:
        row["scraped_at"] = scraped_at
    return rows


def write_outputs(rows: list[dict[str, Any]]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUT_DIR / "fixtech_storefront_latest.json"
    csv_path = OUT_DIR / "fixtech_storefront_latest.csv"
    json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    fieldnames = [
        "retailer",
        "sku",
        "variant_id",
        "product_id",
        "model",
        "storage_gb",
        "storage",
        "color",
        "condition_grade",
        "price_sek",
        "reference_price_sek",
        "currency",
        "stock",
        "url",
        "image_url",
        "scraped_at",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fieldnames})

    print(f"Wrote {len(rows)} rows to {json_path} and {csv_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--all-phones",
        action="store_true",
        help="Include Samsung Galaxy rows as well as iPhone rows.",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    rows = asyncio.run(scrape(include_all_phones=args.all_phones))
    write_outputs(rows)


if __name__ == "__main__":
    main()
