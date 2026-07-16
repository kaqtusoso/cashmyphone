#!/usr/bin/env python3
"""
Scrape Swappie's Swedish storefront inventory/prices.

This is intentionally separate from app/scrapers/swappie.py, which imports
buyback prices for people selling a phone. Swappie's storefront uses different
endpoints and returns sell-to-consumer inventory by SKU.

Outputs:
  data/retail_prices/swappie_storefront_latest.json
  data/retail_prices/swappie_storefront_latest.csv
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

from curl_cffi.requests import AsyncSession


BASE_URL = "https://swappie.com"
COUNTRY_PATH = "se"
COUNTRY_CODE = "SE"
CATEGORY_URL = f"{BASE_URL}/{COUNTRY_PATH}/api/model-search/"
MODEL_URL = f"{BASE_URL}/api/model/{COUNTRY_PATH}/{{model}}"
REFERER = f"{BASE_URL}/{COUNTRY_PATH}/iphone/"
OUT_DIR = Path("data/retail_prices")

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "sv-SE,sv;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": REFERER,
    "Origin": BASE_URL,
}

LOGGER = logging.getLogger("swappie-storefront")


def _amount_to_sek(value: dict[str, Any] | None) -> int | None:
    if not value:
        return None
    amount = value.get("amount")
    precision = value.get("precision", 2)
    if amount is None:
        return None
    return round(float(amount) / (10 ** int(precision)))


async def _get_json(session: AsyncSession, url: str, params: dict[str, Any] | None = None) -> Any:
    response = await session.get(url, params=params, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.json()


async def fetch_models(session: AsyncSession) -> list[str]:
    """Return model names visible on the Swedish iPhone category page."""
    items = await _get_json(
        session,
        CATEGORY_URL,
        {"productCategory": "phone", "sorting": "popular"},
    )
    models = sorted({item["name"] for item in items if item.get("name", "").startswith("iPhone")})
    return models


def parse_phone(phone: dict[str, Any]) -> dict[str, Any] | None:
    model = phone.get("modelName") or phone.get("name")
    sku = phone.get("id")
    price_sek = _amount_to_sek(phone.get("normalPrice"))
    if not model or not sku or not price_sek:
        return None

    slug = phone.get("translatedLangSlug") or phone.get("slug")
    url = f"{BASE_URL}/{COUNTRY_PATH}/iphone/{quote(model.lower().replace(' ', '-'))}/{slug}/" if slug else None

    return {
        "retailer": "swappie",
        "sku": sku,
        "model": model,
        "storage_gb": phone.get("storage"),
        "color": phone.get("color"),
        "condition_grade": phone.get("grade"),
        "battery_type": phone.get("batteryType"),
        "sim_type": phone.get("simType"),
        "price_sek": price_sek,
        "reference_price_sek": _amount_to_sek(phone.get("referencePrice")),
        "currency": phone.get("currency") or "SEK",
        "stock": phone.get("stock", 0),
        "stock_per_warehouse": phone.get("stockPerWarehouse") or {},
        "url": url,
        "variant_deep_link": bool(slug),
        "variant_selection_required": False,
        "variant_url_kind": "sku_path",
        "updated_at": phone.get("updatedAt"),
    }


async def fetch_model_inventory(session: AsyncSession, model: str) -> list[dict[str, Any]]:
    url = MODEL_URL.format(model=quote(model))
    data = await _get_json(session, url)
    rows = [parsed for phone in data.get("availablePhones", []) if (parsed := parse_phone(phone))]
    LOGGER.info("%s: %s storefront SKUs", model, len(rows))
    return rows


async def scrape(models: list[str] | None = None) -> list[dict[str, Any]]:
    async with AsyncSession(impersonate="chrome136") as session:
        selected_models = models or await fetch_models(session)
        LOGGER.info("Scraping %s Swappie storefront models", len(selected_models))

        rows: list[dict[str, Any]] = []
        for model in selected_models:
            try:
                rows.extend(await fetch_model_inventory(session, model))
            except Exception as exc:
                LOGGER.warning("%s failed: %s", model, exc)
            await asyncio.sleep(0.25)

    scraped_at = datetime.now(timezone.utc).isoformat()
    for row in rows:
        row["scraped_at"] = scraped_at
    return rows


def write_outputs(rows: list[dict[str, Any]]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    json_path = OUT_DIR / "swappie_storefront_latest.json"
    csv_path = OUT_DIR / "swappie_storefront_latest.csv"

    json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    fieldnames = [
        "retailer",
        "sku",
        "model",
        "storage_gb",
        "color",
        "condition_grade",
        "battery_type",
        "sim_type",
        "price_sek",
        "reference_price_sek",
        "currency",
        "stock",
        "url",
        "variant_deep_link",
        "variant_selection_required",
        "variant_url_kind",
        "updated_at",
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
        "--model",
        action="append",
        help="Limit scrape to a model, e.g. --model 'iPhone 15'. Can be passed multiple times.",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    rows = asyncio.run(scrape(args.model))
    write_outputs(rows)


if __name__ == "__main__":
    main()
