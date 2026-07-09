#!/usr/bin/env python3
"""
Scrape Fixiphone's Swedish storefront inventory/prices.

This is separate from app/scrapers/fixiphone.py, which imports buyback prices
for people selling a phone. Fixiphone's storefront is Magento and exposes used
phones as individual products on the begagnade-mobiler category page.

Outputs:
  data/retail_prices/fixiphone_storefront_latest.json
  data/retail_prices/fixiphone_storefront_latest.csv
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
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from curl_cffi.requests import AsyncSession


BASE_URL = "https://www.fixiphone.se"
CATEGORY_URL = f"{BASE_URL}/webbshop/begagnade-mobiler.html"
OUT_DIR = Path("data/retail_prices")

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "sv-SE,sv;q=0.9,en-US;q=0.8,en;q=0.7",
    "User-Agent": "Mozilla/5.0",
}

LOGGER = logging.getLogger("fixiphone-storefront")


async def _get_text(session: AsyncSession, url: str) -> str:
    response = await session.get(url, headers=HEADERS, timeout=45)
    response.raise_for_status()
    return response.text


def _parse_storage_gb(text: str | None) -> int | None:
    if not text:
        return None
    match = re.search(r"(\d+)\s*(GB|TB)", text, re.I)
    if not match:
        return None
    amount = int(match.group(1))
    return amount * 1024 if match.group(2).lower() == "tb" else amount


def _parse_name(name: str) -> tuple[str, str | None, str | None]:
    clean = re.sub(r"\s+", " ", name).strip()
    location = None
    condition = None
    if "/" in clean:
        clean, location = [part.strip() for part in clean.split("/", 1)]
    match = re.search(r"\(([^)]+)\)", location or clean)
    if match:
        condition = match.group(1).strip()
        if location:
            location = re.sub(r"\s*\([^)]+\)", "", location).strip()
        else:
            clean = re.sub(r"\s*\([^)]+\)", "", clean).strip()
    model = re.sub(r"\s*-\s*\d+\s*(GB|TB).*$", "", clean, flags=re.I).strip()
    return model.replace("Iphone", "iPhone"), location, condition


def parse_category(html: str, include_all_phones: bool = False) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "lxml")
    rows: list[dict[str, Any]] = []

    for item in soup.select("li.product"):
        link = item.select_one(".product-item-link")
        price_el = item.select_one("[data-price-amount]")
        product_el = item.select_one("[data-product-id]")
        image = item.select_one("img")
        if not link or not price_el:
            continue

        name = link.get_text(" ", strip=True)
        if include_all_phones:
            if not re.search(r"\b(iPhone|Samsung|Sony|OnePlus|Huawei)\b", name, re.I):
                continue
        elif not re.search(r"\biPhone\b", name, re.I):
            continue

        price = price_el.get("data-price-amount")
        model, location, condition = _parse_name(name)
        product_id = product_el.get("data-product-id") if product_el else None
        url = urljoin(BASE_URL, link.get("href"))

        rows.append(
            {
                "retailer": "fixiphone",
                "sku": product_id or url.rstrip("/").rsplit("/", 1)[-1],
                "product_id": product_id,
                "model": model,
                "storage_gb": _parse_storage_gb(name),
                "storage": f"{_parse_storage_gb(name)} GB" if _parse_storage_gb(name) else None,
                "color": None,
                "condition_grade": condition,
                "location": location,
                "price_sek": int(float(price)) if price else None,
                "reference_price_sek": None,
                "currency": "SEK",
                "stock": 1,
                "url": url,
                "image_url": image.get("data-src") or image.get("data-original") or image.get("src") if image else None,
            }
        )
    return rows


async def scrape(include_all_phones: bool = False) -> list[dict[str, Any]]:
    async with AsyncSession(impersonate="chrome136") as session:
        html = await _get_text(session, CATEGORY_URL)
    rows = parse_category(html, include_all_phones=include_all_phones)
    LOGGER.info("Fixiphone category yielded %s storefront SKUs", len(rows))

    scraped_at = datetime.now(timezone.utc).isoformat()
    for row in rows:
        row["scraped_at"] = scraped_at
    return rows


def write_outputs(rows: list[dict[str, Any]]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUT_DIR / "fixiphone_storefront_latest.json"
    csv_path = OUT_DIR / "fixiphone_storefront_latest.csv"
    json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    fieldnames = [
        "retailer",
        "sku",
        "product_id",
        "model",
        "storage_gb",
        "storage",
        "color",
        "condition_grade",
        "location",
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
        help="Include non-iPhone phone rows in the used-phone category.",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    rows = asyncio.run(scrape(include_all_phones=args.all_phones))
    write_outputs(rows)


if __name__ == "__main__":
    main()
