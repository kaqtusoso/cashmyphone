#!/usr/bin/env python3
"""
Scrape FixMyPhone's Swedish storefront inventory/prices.

This is separate from app/scrapers/fixmyphone.py, which imports buyback prices
for people selling a phone. FixMyPhone's storefront is WooCommerce and exposes
sell-to-consumer variant data in data-product_variations on product pages.

Outputs:
  data/retail_prices/fixmyphone_storefront_latest.json
  data/retail_prices/fixmyphone_storefront_latest.csv
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
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup
from curl_cffi.requests import AsyncSession


BASE_URL = "https://fixmyphone.se"
LIST_URL = f"{BASE_URL}/"
OUT_DIR = Path("data/retail_prices")

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "sv-SE,sv;q=0.9,en-US;q=0.8,en;q=0.7",
    "User-Agent": "Mozilla/5.0",
}

COLOR_LABELS = {
    "black": "Black",
    "blue": "Blue",
    "blue-2": "Blue 2",
    "coral": "Coral",
    "gold": "Gold",
    "grafit": "Grafit",
    "green": "Green",
    "midnight": "Midnight",
    "mork-gron": "Mörk grön",
    "naturlig-titanium": "Naturlig titanium",
    "naturligtitanium": "Naturlig titanium",
    "purple": "Purple",
    "red": "Red",
    "rosa": "Rosa",
    "sandfargad-titanium": "Sandfärgad titanium",
    "silver": "Silver",
    "space-grey": "Space grey",
    "starlight": "Starlight",
    "titanium": "Titanium",
    "white": "White",
    "yellow": "Yellow",
}

CONDITION_LABELS = {
    "acceptable": "Acceptable",
    "good": "Good",
    "very-good": "Very good",
    "like-new": "Like new",
}

LOGGER = logging.getLogger("fixmyphone-storefront")


def _variant_url(page_url: str, attributes: dict[str, Any]) -> str:
    parts = urlsplit(page_url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query.update({key: str(value) for key, value in attributes.items() if value})
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


async def _get_text(session: AsyncSession, url: str) -> str:
    last_exc: Exception | None = None
    for attempt in range(3):
        try:
            response = await session.get(url, headers=HEADERS, timeout=45)
            response.raise_for_status()
            return response.text
        except Exception as exc:
            last_exc = exc
            if attempt < 2:
                await asyncio.sleep(1.5 * (attempt + 1))
    raise last_exc


def _labelize_slug(value: str | None) -> str | None:
    if not value:
        return None
    return " ".join(part.capitalize() for part in value.replace("_", "-").split("-") if part)


def _parse_storage_gb(value: str | None) -> int | None:
    if not value:
        return None
    match = re.match(r"^(\d+)-?(gb|tb)$", value.strip(), re.I)
    if not match:
        return None
    amount = int(match.group(1))
    return amount * 1024 if match.group(2).lower() == "tb" else amount


def _storage_label(value: str | None) -> str | None:
    storage_gb = _parse_storage_gb(value)
    if storage_gb is None:
        return None
    return "1 TB" if storage_gb == 1024 else f"{storage_gb} GB"


def _extract_stock(variant: dict[str, Any]) -> int:
    if not variant.get("is_in_stock"):
        return 0
    max_qty = variant.get("max_qty")
    if isinstance(max_qty, int):
        return max_qty
    if isinstance(max_qty, str) and max_qty.isdigit():
        return int(max_qty)
    return 1


def parse_model_links(html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    links: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        href = urljoin(BASE_URL, anchor["href"]).split("#")[0]
        lowered = href.lower()
        if not lowered.startswith(f"{BASE_URL}/iphone"):
            continue
        if any(token in lowered for token in ("pre-loved", "begagnad", "fornyad")):
            links.add(href if href.endswith("/") else f"{href}/")
    return sorted(links)


def _extract_model_name(soup: BeautifulSoup, url: str) -> str:
    h1 = soup.find("h1")
    if h1:
        text = h1.get_text(" ", strip=True)
        text = re.sub(r"\s+Begagnad.*$", "", text, flags=re.I).strip()
        if text:
            return text.replace("IPhone", "iPhone")
    slug = url.rstrip("/").rsplit("/", 1)[-1]
    slug = re.sub(r"-(pre-loved|begagnad|fornyad-begagnad.*)$", "", slug, flags=re.I)
    return " ".join(part.upper() if part == "se" else part.capitalize() for part in slug.split("-")).replace("Iphone", "iPhone")


def parse_product_page(html: str, page_url: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "lxml")
    form = soup.find(attrs={"data-product_variations": True})
    if not form:
        return []

    model = _extract_model_name(soup, page_url)
    variants = json.loads(html_lib.unescape(form.get("data-product_variations") or "[]"))
    rows: list[dict[str, Any]] = []

    for variant in variants:
        stock = _extract_stock(variant)
        if stock <= 0 or not variant.get("is_purchasable"):
            continue
        attrs = variant.get("attributes") or {}
        storage_slug = attrs.get("attribute_pa_capacity")
        color_slug = attrs.get("attribute_pa_color")
        condition_slug = attrs.get("attribute_pa_condition")
        price = variant.get("display_price")
        regular_price = variant.get("display_regular_price")
        image = variant.get("image") or {}

        rows.append(
            {
                "retailer": "fixmyphone",
                "sku": variant.get("sku") or variant.get("variation_id"),
                "variation_id": variant.get("variation_id"),
                "model": model,
                "storage_gb": _parse_storage_gb(storage_slug),
                "storage": _storage_label(storage_slug),
                "color": COLOR_LABELS.get(color_slug, _labelize_slug(color_slug)),
                "condition_grade": CONDITION_LABELS.get(condition_slug, _labelize_slug(condition_slug)),
                "price_sek": int(price) if price is not None else None,
                "reference_price_sek": int(regular_price) if regular_price and regular_price != price else None,
                "currency": "SEK",
                "stock": stock,
                "url": _variant_url(page_url, attrs),
                "variant_deep_link": bool(storage_slug and color_slug and condition_slug),
                "variant_selection_required": False,
                "variant_url_kind": "woocommerce_attributes",
                "image_url": image.get("url") or image.get("src"),
            }
        )
    return rows


async def fetch_model_inventory(session: AsyncSession, url: str) -> list[dict[str, Any]]:
    html = await _get_text(session, url)
    rows = parse_product_page(html, url)
    LOGGER.info("%s: %s stocked storefront SKUs", url.rstrip("/").rsplit("/", 1)[-1], len(rows))
    return rows


async def scrape(urls: list[str] | None = None) -> list[dict[str, Any]]:
    async with AsyncSession(impersonate="chrome136") as session:
        selected_urls = urls or parse_model_links(await _get_text(session, LIST_URL))
        LOGGER.info("Scraping %s FixMyPhone storefront candidates", len(selected_urls))

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
    json_path = OUT_DIR / "fixmyphone_storefront_latest.json"
    csv_path = OUT_DIR / "fixmyphone_storefront_latest.csv"
    json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    fieldnames = [
        "retailer",
        "sku",
        "variation_id",
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
        "variant_deep_link",
        "variant_selection_required",
        "variant_url_kind",
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
    parser.add_argument("--url", action="append", help="Limit scrape to a product URL. Can be passed multiple times.")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    rows = asyncio.run(scrape(args.url))
    write_outputs(rows)


if __name__ == "__main__":
    main()
