#!/usr/bin/env python3
"""
Build a normalized used-phone catalog from retailer storefront snapshots.

The storefront scrapers write one latest JSON snapshot per retailer under
data/retail_prices. This script combines those snapshots into a frontend/API
friendly catalog for Televera's buy-side comparison pages.

Outputs:
  data/retail_prices/used_phone_catalog_latest.json
  data/retail_prices/used_phone_catalog_latest.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.pricing.iphone_catalog import VALID_STORAGE_BY_MODEL_GB, is_valid_storage_for_model


DEFAULT_INPUT_DIR = Path("data/retail_prices")
DEFAULT_OUTPUT_DIR = Path("data/retail_prices")
INPUT_GLOB = "*_storefront_latest.json"

RETAILER_LABELS = {
    "fixiphone": "Fixiphone",
    "fixmyphone": "FixMyPhone",
    "fixtech": "FixTech",
    "happyphone": "HappyPhone",
    "phonehero": "PhoneHero",
    "renewed": "ReNewed",
    "swappie": "Swappie",
    "telestore": "Telestore",
}

CONDITION_LABEL_BY_TIER = {
    "new_like": "Nyskick",
    "excellent": "Utmärkt skick",
    "very_good": "Mycket bra skick",
    "good": "Bra skick",
    "fair": "Okej skick",
    "unknown": "Ej angivet",
}

KNOWN_MODEL_DISPLAY_BY_KEY = {
    key: " ".join("iPhone" if part == "iphone" else part.upper() if part == "se" else part.capitalize() for part in key.split())
    for key in VALID_STORAGE_BY_MODEL_GB
}
KNOWN_MODEL_DISPLAY_BY_KEY.update(
    {
        "iphone air": "iPhone Air",
        "iphone 16e": "iPhone 16e",
        "iphone 17e": "iPhone 17e",
    }
)
KNOWN_MODEL_KEYS_BY_LENGTH = sorted(KNOWN_MODEL_DISPLAY_BY_KEY, key=len, reverse=True)


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = re.sub(r"\s+", " ", str(value)).strip()
    return text or None


def slugify(value: str) -> str:
    text = value.lower()
    text = text.replace("å", "a").replace("ä", "a").replace("ö", "o")
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def storage_label(storage_gb: int | None) -> str | None:
    if storage_gb is None:
        return None
    if storage_gb % 1024 == 0 and storage_gb >= 1024:
        return f"{storage_gb // 1024} TB"
    return f"{storage_gb} GB"


def parse_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(float(str(value).replace(" ", "").replace(",", ".")))
    except (TypeError, ValueError):
        return None


def normalize_model(raw_model: Any) -> str | None:
    model = _clean_text(raw_model)
    if not model:
        return None

    model = re.sub(r"^Apple\s+", "", model, flags=re.I)
    model = re.sub(r"\biPhone\s+SE\s*\((2020|2022)\)", r"iPhone SE \1", model, flags=re.I)
    model = model.replace("Iphone", "iPhone")
    model_key = model.lower()
    model_key = re.sub(r"[^a-z0-9]+", " ", model_key)
    model_key = re.sub(r"\s+", " ", model_key).strip()

    for known_key in KNOWN_MODEL_KEYS_BY_LENGTH:
        if re.search(rf"(^|\s){re.escape(known_key)}($|\s)", model_key):
            return KNOWN_MODEL_DISPLAY_BY_KEY[known_key]

    if model_key.startswith("iphone"):
        return " ".join("iPhone" if part == "iphone" else part.upper() if part == "se" else part.capitalize() for part in model_key.split())
    return None


def normalize_condition_tier(raw_condition: Any) -> str:
    condition = (_clean_text(raw_condition) or "").lower()
    condition = condition.replace("(", " ").replace(")", " ")

    if any(token in condition for token in ("nyskick", "som ny", "like new", "like-new", "klass a", "helt ny", "premium")):
        return "new_like"
    if any(token in condition for token in ("utmärkt", "utmärkt skick", "excellent")):
        return "excellent"
    if any(token in condition for token in ("mycket bra", "very good", "very-good", "klass b")):
        return "very_good"
    if any(token in condition for token in ("bra", "good", "klass c")):
        return "good"
    if any(token in condition for token in ("okej", "acceptable", "fair", "klass d")):
        return "fair"
    return "unknown"


def normalize_color(raw_color: Any) -> str | None:
    color = _clean_text(raw_color)
    if not color:
        return None
    color = re.sub(r"^\|\s*", "", color)
    color = re.split(r"\s*(?:,|-)?\s*(?:grade\s+[a-d]|batteri|som ny)\b", color, maxsplit=1, flags=re.I)[0]
    color = color.strip(" ,|")
    if not color:
        return None
    replacements = {
        "black": "Svart",
        "white": "Vit",
        "red": "Röd",
        "yellow": "Gul",
        "green": "Grön",
        "blue": "Blå",
        "purple": "Lila",
        "silver": "Silver",
        "gold": "Guld",
        "space grey": "Rymdgrå",
        "space gray": "Rymdgrå",
        "midnight": "Midnatt",
        "starlight": "Stjärnglans",
        "grafit": "Grafit",
        "graphite": "Grafit",
    }
    return replacements.get(color.lower(), color[:1].upper() + color[1:])


def extract_battery_health(*values: Any) -> str | None:
    for value in values:
        text = _clean_text(value)
        if not text:
            continue
        if re.fullmatch(r"\d{2,3}%?", text):
            return text if text.endswith("%") else f"{text}%"
        match = re.search(r"batteri\s*%?\s*(\d{2,3})\s*%?", text, re.I)
        if match:
            return f"{match.group(1)}%"
    return None


def normalize_offer(row: dict[str, Any], source_file: Path) -> dict[str, Any] | None:
    retailer = _clean_text(row.get("retailer"))
    sku = _clean_text(row.get("sku"))
    model = normalize_model(row.get("model"))
    storage_gb = parse_int(row.get("storage_gb"))
    price_sek = parse_int(row.get("price_sek"))
    stock = parse_int(row.get("stock"))
    url = _clean_text(row.get("url"))

    if not retailer or not sku or not model or not price_sek or not url:
        return None
    if stock is not None and stock <= 0:
        return None
    if not is_valid_storage_for_model(model, storage_gb):
        return None

    condition_raw = _clean_text(row.get("condition_grade"))
    condition_tier = normalize_condition_tier(condition_raw)
    battery_type = _clean_text(row.get("battery_type"))
    battery_health = extract_battery_health(row.get("battery_health"), row.get("color"), row.get("condition_grade"))
    reference_price_sek = parse_int(row.get("reference_price_sek"))
    offer_id = slugify(f"{retailer}-{sku}-{model}-{storage_gb or 'na'}")

    return {
        "id": offer_id,
        "retailer": retailer,
        "retailer_label": RETAILER_LABELS.get(retailer, retailer.title()),
        "sku": sku,
        "model": model,
        "model_slug": slugify(model),
        "storage_gb": storage_gb,
        "storage": storage_label(storage_gb) or _clean_text(row.get("storage")),
        "color": normalize_color(row.get("color")),
        "condition_raw": condition_raw,
        "condition_tier": condition_tier,
        "condition_label": CONDITION_LABEL_BY_TIER[condition_tier],
        "battery_type": battery_type,
        "battery_health": battery_health,
        "has_new_battery": bool(battery_type and "nytt batteri" in battery_type.lower()),
        "price_sek": price_sek,
        "reference_price_sek": reference_price_sek,
        "currency": _clean_text(row.get("currency")) or "SEK",
        "stock": stock if stock is not None else 1,
        "lead_url": url,
        "image_url": _clean_text(row.get("image_url")),
        "scraped_at": _clean_text(row.get("scraped_at")),
        "source_file": source_file.name,
    }


def load_offers(input_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    offers_by_id: dict[str, dict[str, Any]] = {}
    source_files: list[dict[str, Any]] = []

    for path in sorted(input_dir.glob(INPUT_GLOB)):
        if path.name.startswith("used_phone_catalog_"):
            continue
        rows = json.loads(path.read_text())
        source_files.append({"file": path.name, "rows": len(rows)})
        for row in rows:
            offer = normalize_offer(row, path)
            if not offer:
                continue
            existing = offers_by_id.get(offer["id"])
            if existing is None or offer["price_sek"] < existing["price_sek"]:
                offers_by_id[offer["id"]] = offer

    offers = sorted(
        offers_by_id.values(),
        key=lambda offer: (offer["model_slug"], offer["price_sek"], offer["retailer_label"], offer["id"]),
    )
    return offers, source_files


def build_model_summaries(offers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    by_model: dict[str, list[dict[str, Any]]] = {}
    for offer in offers:
        by_model.setdefault(offer["model"], []).append(offer)

    for model, model_offers in sorted(by_model.items(), key=lambda item: item[0].lower()):
        prices = [offer["price_sek"] for offer in model_offers]
        summaries.append(
            {
                "model": model,
                "model_slug": slugify(model),
                "offer_count": len(model_offers),
                "retailer_count": len({offer["retailer"] for offer in model_offers}),
                "min_price_sek": min(prices),
                "max_price_sek": max(prices),
                "storage_options_gb": sorted({offer["storage_gb"] for offer in model_offers if offer["storage_gb"] is not None}),
                "condition_tiers": sorted({offer["condition_tier"] for offer in model_offers}),
                "colors": sorted({offer["color"] for offer in model_offers if offer["color"]}),
            }
        )
    return summaries


def build_filter_options(offers: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "models": build_model_summaries(offers),
        "retailers": [
            {"value": value, "label": label}
            for value, label in sorted(
                {
                    offer["retailer"]: offer["retailer_label"]
                    for offer in offers
                }.items(),
                key=lambda item: item[1].lower(),
            )
        ],
        "storage_options_gb": sorted({offer["storage_gb"] for offer in offers if offer["storage_gb"] is not None}),
        "condition_tiers": [
            {"value": tier, "label": label}
            for tier, label in CONDITION_LABEL_BY_TIER.items()
            if any(offer["condition_tier"] == tier for offer in offers)
        ],
    }


def write_json_catalog(output_dir: Path, offers: list[dict[str, Any]], source_files: list[dict[str, Any]]) -> Path:
    generated_at = datetime.now(timezone.utc).isoformat()
    catalog = {
        "generated_at": generated_at,
        "total_offers": len(offers),
        "source_files": source_files,
        "filter_options": build_filter_options(offers),
        "models": build_model_summaries(offers),
        "offers": offers,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "used_phone_catalog_latest.json"
    path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n")
    return path


def write_csv_catalog(output_dir: Path, offers: list[dict[str, Any]]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "used_phone_catalog_latest.csv"
    fieldnames = [
        "id",
        "retailer",
        "retailer_label",
        "sku",
        "model",
        "model_slug",
        "storage_gb",
        "storage",
        "color",
        "condition_raw",
        "condition_tier",
        "condition_label",
        "battery_type",
        "battery_health",
        "has_new_battery",
        "price_sek",
        "reference_price_sek",
        "currency",
        "stock",
        "lead_url",
        "image_url",
        "scraped_at",
        "source_file",
    ]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(offers)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Televera's normalized used-phone catalog")
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    offers, source_files = load_offers(args.input_dir)
    json_path = write_json_catalog(args.output_dir, offers, source_files)
    csv_path = write_csv_catalog(args.output_dir, offers)
    models = build_model_summaries(offers)
    print(f"Wrote {len(offers)} offers across {len(models)} models")
    print(f"JSON: {json_path}")
    print(f"CSV: {csv_path}")


if __name__ == "__main__":
    main()
