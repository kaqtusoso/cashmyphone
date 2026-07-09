#!/usr/bin/env python3
"""
Scrape reNewed's Swedish storefront inventory/prices.

This is separate from app/scrapers/renewed.py, which imports buyback prices for
people selling a phone. reNewed's storefront is Shopify, where public collection
JSON exposes product variants with price and availability.

Outputs:
  data/retail_prices/renewed_storefront_latest.json
  data/retail_prices/renewed_storefront_latest.csv
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


BASE_URL = "https://renewed.se"
DEFAULT_COLLECTION = "all"
OUT_DIR = Path("data/retail_prices")

HEADERS = {
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "sv-SE,sv;q=0.9,en-US;q=0.8,en;q=0.7",
    "User-Agent": "Mozilla/5.0",
}

LOGGER = logging.getLogger("renewed-storefront")

ACCESSORY_KEYWORDS = (
    "skal",
    "mobilskal",
    "fodral",
    "skärmskydd",
    "skarmskydd",
    "laddare",
    "laddningskabel",
    "adapter",
    "hörlur",
    "airpods",
    "magsafe",
)


async def _get_json(session: AsyncSession, url: str, params: dict[str, Any]) -> dict[str, Any]:
    response = await session.get(url, params=params, headers=HEADERS, timeout=45)
    response.raise_for_status()
    return response.json()


def _parse_price(value: Any) -> int | None:
    if value in (None, ""):
        return None
    if isinstance(value, str):
        value = value.replace("\xa0", "").replace(" ", "").replace(",", ".")
        return round(float(value))
    if isinstance(value, int):
        return round(value / 100) if value > 100000 else value
    if isinstance(value, float):
        return round(value / 100) if value > 100000 else round(value)
    return None


def _parse_storage_gb(text: str | None) -> int | None:
    if not text:
        return None
    match = re.search(r"(\d+)\s*(GB|TB)", text, re.I)
    if not match:
        return None
    amount = int(match.group(1))
    return amount * 1024 if match.group(2).lower() == "tb" else amount


def _normalize_storage(text: str | None) -> str | None:
    storage_gb = _parse_storage_gb(text)
    if storage_gb is None:
        return None
    return "1 TB" if storage_gb == 1024 else f"{storage_gb} GB"


def _clean_model(title: str) -> str:
    model = re.sub(r"\s+-\s*(PREMIUM|Kampanj)\s*$", "", title, flags=re.I)
    model = re.sub(r"\s+", " ", model).strip()
    return model.replace("Iphone", "iPhone")


def _is_accessory(title: str) -> bool:
    lowered = title.lower()
    return any(keyword in lowered for keyword in ACCESSORY_KEYWORDS)


def _product_url(handle: str | None) -> str:
    return f"{BASE_URL}/products/{handle}" if handle else BASE_URL


def _image_url(variant: dict[str, Any], product: dict[str, Any]) -> str | None:
    featured = variant.get("featured_image") or {}
    if featured.get("src"):
        return featured.get("src")
    images = product.get("images") or []
    if images:
        first = images[0]
        return first.get("src") if isinstance(first, dict) else first
    return None


def _option_map(product: dict[str, Any], variant: dict[str, Any]) -> dict[str, str | None]:
    result: dict[str, str | None] = {}
    for index, option in enumerate(product.get("options") or [], start=1):
        name = option.get("name") if isinstance(option, dict) else str(option)
        result[name.lower()] = variant.get(f"option{index}")
    return result


def parse_products(products: list[dict[str, Any]], include_all_phones: bool = False) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen_variant_ids: set[str] = set()

    for product in products:
        title = product.get("title") or ""
        if _is_accessory(title):
            continue
        if include_all_phones:
            if not re.search(r"\b(iPhone|Samsung Galaxy)\b", title, re.I):
                continue
        elif not re.search(r"\biPhone\b", title, re.I):
            continue

        product_id = product.get("id")
        handle = product.get("handle")
        model = _clean_model(title)
        product_label = None
        label_match = re.search(r"\s+-\s*(PREMIUM|Kampanj)\s*$", title, re.I)
        if label_match:
            product_label = label_match.group(1)

        for variant in product.get("variants") or []:
            if not variant.get("available"):
                continue
            variant_id = str(variant.get("id") or "")
            if variant_id and variant_id in seen_variant_ids:
                continue
            seen_variant_ids.add(variant_id)

            options = _option_map(product, variant)
            storage = options.get("kapacitet") or _normalize_storage(variant.get("title"))
            condition = options.get("skick") or product_label
            if product_label and condition and product_label.lower() not in condition.lower():
                condition = f"{condition} ({product_label})"

            price_sek = _parse_price(variant.get("price"))
            if not price_sek:
                continue

            rows.append(
                {
                    "retailer": "renewed",
                    "sku": variant.get("sku") or variant_id,
                    "variant_id": variant.get("id"),
                    "product_id": product_id,
                    "model": model,
                    "storage_gb": _parse_storage_gb(storage or variant.get("title")),
                    "storage": _normalize_storage(storage or variant.get("title")),
                    "color": options.get("färg"),
                    "condition_grade": condition,
                    "price_sek": price_sek,
                    "reference_price_sek": _parse_price(variant.get("compare_at_price")),
                    "currency": "SEK",
                    "stock": 1,
                    "url": _product_url(handle),
                    "image_url": _image_url(variant, product),
                }
            )
    return rows


async def scrape(collection: str = DEFAULT_COLLECTION, include_all_phones: bool = False) -> list[dict[str, Any]]:
    products: list[dict[str, Any]] = []
    async with AsyncSession(impersonate="chrome136") as session:
        page = 1
        while True:
            url = f"{BASE_URL}/collections/{collection}/products.json"
            data = await _get_json(session, url, {"limit": 250, "page": page})
            batch = data.get("products") or []
            if not batch:
                break
            LOGGER.info("Fetched %s products from collection %s page %s", len(batch), collection, page)
            products.extend(batch)
            if len(batch) < 250:
                break
            page += 1
            await asyncio.sleep(0.25)

    rows = parse_products(products, include_all_phones=include_all_phones)
    scraped_at = datetime.now(timezone.utc).isoformat()
    for row in rows:
        row["scraped_at"] = scraped_at
    return rows


def write_outputs(rows: list[dict[str, Any]]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUT_DIR / "renewed_storefront_latest.json"
    csv_path = OUT_DIR / "renewed_storefront_latest.csv"
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
        "--collection",
        default=DEFAULT_COLLECTION,
        help="Shopify collection handle to scrape. Defaults to all.",
    )
    parser.add_argument(
        "--all-phones",
        action="store_true",
        help="Include Samsung Galaxy rows as well as iPhone rows.",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    rows = asyncio.run(scrape(collection=args.collection, include_all_phones=args.all_phones))
    write_outputs(rows)


if __name__ == "__main__":
    main()
