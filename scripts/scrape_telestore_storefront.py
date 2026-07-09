#!/usr/bin/env python3
"""
Scrape Telestore's Swedish storefront inventory/prices.

This is separate from app/scrapers/telestore.py, which imports buyback prices
for people selling a phone. Telestore's storefront exposes sell-to-consumer
variant data in a productData object on each model page.

Outputs:
  data/retail_prices/telestore_storefront_latest.json
  data/retail_prices/telestore_storefront_latest.csv
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


BASE_URL = "https://telestore.se"
CATEGORY_URL = f"{BASE_URL}/begagnade-mobiler/iphone/"
OUT_DIR = Path("data/retail_prices")

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "sv-SE,sv;q=0.9,en-US;q=0.8,en;q=0.7",
    "User-Agent": "Mozilla/5.0",
}

LOGGER = logging.getLogger("telestore-storefront")


async def _get_text(session: AsyncSession, url: str) -> str:
    response = await session.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.text


def _extract_product_data(html: str) -> dict[str, Any] | None:
    match = re.search(r"var\s+productData\s*=\s*(\{.*?\});\s*</script>", html, re.S)
    if not match:
        return None
    return json.loads(match.group(1))


def _parse_storage_gb(label: str | None) -> int | None:
    if not label:
        return None
    match = re.search(r"(\d+)\s*GB", label, re.I)
    if match:
        return int(match.group(1))
    match = re.search(r"(\d+)\s*TB", label, re.I)
    return int(match.group(1)) * 1024 if match else None


def _split_options(option_labels: list[str]) -> tuple[str | None, str | None, str | None]:
    storage = next((value for value in option_labels if re.search(r"\d+\s*GB", value, re.I)), None)
    condition = next(
        (
            value
            for value in option_labels
            if value in {"Helt ny", "Premium", "Klass A", "Klass B", "Klass C"}
        ),
        None,
    )
    color = next((value for value in option_labels if value not in {storage, condition}), None)
    return storage, condition, color


def parse_product_page(html: str, page_url: str) -> list[dict[str, Any]]:
    data = _extract_product_data(html)
    if not data:
        return []

    titles = {int(key): value for key, value in data.get("optionsTitles", {}).items()}
    model = data.get("productTitle")
    stocked_option_ids = {tuple(ids) for ids in data.get("stockedOptionIDs", [])}

    rows: list[dict[str, Any]] = []
    for combination in data.get("combinations", []):
        option_ids = combination.get("optionIDs") or []
        stock = int(combination.get("stock") or 0)
        if stock <= 0 and tuple(option_ids) not in stocked_option_ids:
            continue

        labels = [titles[option_id] for option_id in option_ids if option_id in titles]
        storage_label, condition, color = _split_options(labels)
        campaign_price = combination.get("campaignPrice")
        normal_price = combination.get("price")
        price = campaign_price or normal_price

        rows.append(
            {
                "retailer": "telestore",
                "sku": combination.get("articleNumber") or combination.get("id"),
                "model": model,
                "storage_gb": _parse_storage_gb(storage_label),
                "storage": storage_label,
                "color": color,
                "condition_grade": condition,
                "battery_health": combination.get("battery") or None,
                "price_sek": int(price) if price else None,
                "reference_price_sek": int(normal_price) if normal_price else None,
                "currency": "SEK",
                "stock": stock,
                "url": page_url,
            }
        )
    return rows


def parse_model_links(html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    links: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        href = urljoin(BASE_URL, anchor["href"]).split("#")[0]
        if "/begagnade-mobiler/iphone/" not in href:
            continue
        if href.rstrip("/") == CATEGORY_URL.rstrip("/"):
            continue
        links.add(href if href.endswith("/") else f"{href}/")
    return sorted(links)


async def fetch_model_inventory(session: AsyncSession, url: str) -> list[dict[str, Any]]:
    html = await _get_text(session, url)
    rows = parse_product_page(html, url)
    LOGGER.info("%s: %s stocked storefront SKUs", url.rstrip("/").rsplit("/", 1)[-1], len(rows))
    return rows


async def scrape(urls: list[str] | None = None) -> list[dict[str, Any]]:
    async with AsyncSession(impersonate="chrome136") as session:
        selected_urls = urls
        if not selected_urls:
            selected_urls = parse_model_links(await _get_text(session, CATEGORY_URL))
        LOGGER.info("Scraping %s Telestore storefront models", len(selected_urls))

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
    json_path = OUT_DIR / "telestore_storefront_latest.json"
    csv_path = OUT_DIR / "telestore_storefront_latest.csv"

    json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    fieldnames = [
        "retailer",
        "sku",
        "model",
        "storage_gb",
        "storage",
        "color",
        "condition_grade",
        "battery_health",
        "price_sek",
        "reference_price_sek",
        "currency",
        "stock",
        "url",
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
