#!/usr/bin/env python3
"""
Scrape PhoneHero's Swedish storefront inventory/prices.

This is separate from app/scrapers/phonehero.py, which imports buyback prices
for people selling a phone. PhoneHero's storefront exposes sell-to-consumer
SKU data in Livewire snapshots on each model page.

Outputs:
  data/retail_prices/phonehero_storefront_latest.json
  data/retail_prices/phonehero_storefront_latest.csv
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import html as html_lib
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from curl_cffi.requests import AsyncSession


BASE_URL = "https://phonehero.se"
CATEGORY_URL = f"{BASE_URL}/begagnade-mobiler/Apple"
OUT_DIR = Path("data/retail_prices")

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "sv-SE,sv;q=0.9,en-US;q=0.8,en;q=0.7",
    "User-Agent": "Mozilla/5.0",
}

LOGGER = logging.getLogger("phonehero-storefront")


async def _get_text(session: AsyncSession, url: str) -> str:
    response = await session.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.text


def _parse_storage_gb(label: str | None) -> int | None:
    if not label:
        return None
    match = re.search(r"(\d+)\s*GB", label, re.I)
    if match:
        return int(match.group(1))
    match = re.search(r"(\d+)\s*TB", label, re.I)
    return int(match.group(1)) * 1024 if match else None


def _parse_battery_type(name: str | None) -> str | None:
    if not name:
        return None
    if "Nytt batteri original" in name:
        return "Nytt batteri original"
    if "Nytt batteri" in name:
        return "Nytt batteri"
    return None


def _parse_model_from_name(name: str | None, storage: str | None, condition: str | None, color: str | None) -> str | None:
    if not name:
        return None
    model = name
    for value in (color, storage, condition, _parse_battery_type(name)):
        if value:
            model = model.replace(value, "")
    model = re.sub(r"\s+", " ", model).strip()
    return model or None


def parse_model_links(html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    links: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        href = urljoin(BASE_URL, anchor["href"]).split("#")[0]
        if "/begagnade-mobiler/Apple/" not in href:
            continue
        links.add(href)
    return sorted(links)


def _livewire_snapshots(html: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "lxml")
    snapshots: list[dict[str, Any]] = []
    for element in soup.select("[wire\\:snapshot]"):
        raw = html_lib.unescape(element.get("wire:snapshot") or "")
        try:
            snapshots.append(json.loads(raw))
        except json.JSONDecodeError:
            continue
    return snapshots


def parse_product_page(html: str, page_url: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for snapshot in _livewire_snapshots(html):
        if snapshot.get("memo", {}).get("name") != "deviceselector":
            continue
        skus_json = snapshot.get("data", {}).get("skusJson")
        if not skus_json:
            continue
        products = json.loads(skus_json)
        for product in products:
            sku = product.get("sku")
            price = product.get("price")
            discount = product.get("discount") or 0
            storage = product.get("variant")
            condition = product.get("condition")
            color = product.get("color")
            battery_type = _parse_battery_type(product.get("name"))
            rows.append(
                {
                    "retailer": "phonehero",
                    "sku": sku,
                    "model": _parse_model_from_name(product.get("name"), storage, condition, color),
                    "storage_gb": _parse_storage_gb(storage),
                    "storage": storage,
                    "color": color,
                    "condition_grade": condition,
                    "battery_type": battery_type,
                    "price_sek": int(price) if price is not None else None,
                    "reference_price_sek": int(price + discount) if price is not None and discount else None,
                    "currency": "SEK",
                    "stock": 1,
                    "url": page_url,
                    "image_url": product.get("image"),
                }
            )
        break
    return rows


async def fetch_model_inventory(session: AsyncSession, url: str) -> list[dict[str, Any]]:
    html = await _get_text(session, url)
    rows = parse_product_page(html, url)
    LOGGER.info("%s: %s storefront SKUs", url.rstrip("/").rsplit("/", 1)[-1], len(rows))
    return rows


async def scrape(urls: list[str] | None = None) -> list[dict[str, Any]]:
    async with AsyncSession(impersonate="chrome136") as session:
        selected_urls = urls
        if not selected_urls:
            selected_urls = parse_model_links(await _get_text(session, CATEGORY_URL))
        LOGGER.info("Scraping %s PhoneHero storefront models", len(selected_urls))

        rows: list[dict[str, Any]] = []
        for url in selected_urls:
            try:
                rows.extend(await fetch_model_inventory(session, url))
            except Exception as exc:
                LOGGER.warning("%s failed: %s", url, exc)
            await asyncio.sleep(0.25)

    scraped_at = datetime.now(timezone.utc).isoformat()
    for row in rows:
        row["scraped_at"] = scraped_at
    return rows


def write_outputs(rows: list[dict[str, Any]]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUT_DIR / "phonehero_storefront_latest.json"
    csv_path = OUT_DIR / "phonehero_storefront_latest.csv"

    json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    fieldnames = [
        "retailer",
        "sku",
        "model",
        "storage_gb",
        "storage",
        "color",
        "condition_grade",
        "battery_type",
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
        "--url",
        action="append",
        help="Limit scrape to a model URL. Can be passed multiple times.",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    rows = asyncio.run(scrape(args.url))
    write_outputs(rows)


if __name__ == "__main__":
    main()
