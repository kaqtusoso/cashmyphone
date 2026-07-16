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
from scripts.used_phone_conditions import CONDITION_CLASSES, map_used_phone_condition


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

EXCLUDED_RETAILERS = {"fixiphone"}

CONDITION_LABEL_BY_TIER = {
    "new_like": "Nyskick",
    "excellent": "Utmärkt skick",
    "very_good": "Mycket bra skick",
    "good": "Bra skick",
    "fair": "Okej skick",
    "unknown": "Oklart",
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
        "iphone 13 mini": "iPhone 13 Mini",
        "iphone 12 mini": "iPhone 12 Mini",
        "iphone xs max": "iPhone XS Max",
        "iphone xs": "iPhone XS",
        "iphone xr": "iPhone XR",
    }
)
KNOWN_MODEL_KEYS_BY_LENGTH = sorted(KNOWN_MODEL_DISPLAY_BY_KEY, key=len, reverse=True)

# Keep buy-side retailer colors aligned with the model-specific color catalog
# used by the sell flow. Retailers often use generic names such as "White"
# even when Apple only sold that model as Silver.
MODEL_COLOR_KEYS = {
    "iPhone 17e": ("black", "white", "soft_pink"),
    "iPhone Air": ("space_black", "cloud_white", "light_gold", "sky_blue"),
    "iPhone 17 Pro Max": ("deep_blue", "cosmic_orange", "silver"),
    "iPhone 17 Pro": ("deep_blue", "cosmic_orange", "silver"),
    "iPhone 17": ("black", "white", "mist_blue", "sage", "lavender"),
    "iPhone 16e": ("black", "white"),
    "iPhone 16 Pro Max": ("black_titanium", "white_titanium", "natural_titanium", "desert_titanium"),
    "iPhone 16 Pro": ("black_titanium", "white_titanium", "natural_titanium", "desert_titanium"),
    "iPhone 16 Plus": ("black", "white", "pink", "teal", "ultramarine"),
    "iPhone 16": ("black", "white", "pink", "teal", "ultramarine"),
    "iPhone 15 Pro Max": ("black_titanium", "white_titanium", "blue_titanium", "natural_titanium"),
    "iPhone 15 Pro": ("black_titanium", "white_titanium", "blue_titanium", "natural_titanium"),
    "iPhone 15 Plus": ("black", "blue", "green", "yellow", "pink"),
    "iPhone 15": ("black", "blue", "green", "yellow", "pink"),
    "iPhone 14 Pro Max": ("space_black", "silver", "gold", "deep_purple"),
    "iPhone 14 Pro": ("space_black", "silver", "gold", "deep_purple"),
    "iPhone 14 Plus": ("midnight", "starlight", "blue", "purple", "red", "yellow"),
    "iPhone 14": ("midnight", "starlight", "blue", "purple", "red", "yellow"),
    "iPhone 13 Pro Max": ("sierra_blue", "silver", "gold", "graphite", "alpine_green"),
    "iPhone 13 Pro": ("sierra_blue", "silver", "gold", "graphite", "alpine_green"),
    "iPhone 13 Mini": ("green", "pink", "blue", "midnight", "starlight", "red"),
    "iPhone 13": ("green", "pink", "blue", "midnight", "starlight", "red"),
    "iPhone 12 Pro Max": ("silver", "graphite", "gold", "pacific_blue"),
    "iPhone 12 Pro": ("silver", "graphite", "gold", "pacific_blue"),
    "iPhone 12 Mini": ("black", "white", "red", "green", "blue", "purple"),
    "iPhone 12": ("black", "white", "red", "green", "blue", "purple"),
    "iPhone 11 Pro Max": ("midnight_green", "space_grey", "silver", "gold"),
    "iPhone 11 Pro": ("midnight_green", "space_grey", "silver", "gold"),
    "iPhone 11": ("purple", "yellow", "green", "black", "white", "red"),
    "iPhone SE 2022": ("midnight", "starlight", "red"),
    "iPhone SE 2020": ("black", "white", "red"),
    "iPhone XS Max": ("gold", "space_grey", "silver"),
    "iPhone XS": ("gold", "space_grey", "silver"),
    "iPhone XR": ("black", "white", "blue", "yellow", "coral", "red"),
    "iPhone X": ("silver", "space_grey"),
    "iPhone 8 Plus": ("gold", "silver", "space_grey", "red"),
    "iPhone 8": ("gold", "silver", "space_grey", "red"),
    "iPhone 7 Plus": ("black", "gold", "jet_black", "red", "silver", "rose_gold"),
    "iPhone 7": ("black", "gold", "jet_black", "red", "silver", "rose_gold"),
}

COLOR_LABEL_BY_KEY = {
    "alpine_green": "Alpingrön", "black": "Svart", "black_titanium": "Svart titan",
    "blue": "Blå", "blue_titanium": "Blått titan", "cloud_white": "Molnvit",
    "coral": "Korall", "cosmic_orange": "Kosmisk orange", "deep_blue": "Djupblå",
    "deep_purple": "Djuplila", "desert_titanium": "Ökentitan", "gold": "Guld",
    "graphite": "Grafit", "green": "Grön", "jet_black": "Jetsvart", "lavender": "Lavendel",
    "light_gold": "Ljust guld", "midnight": "Midnatt", "midnight_green": "Midnattsgrön",
    "mist_blue": "Dimblå", "natural_titanium": "Naturligt titan", "pacific_blue": "Havsblå",
    "pink": "Rosa", "purple": "Lila", "red": "Röd", "rose_gold": "Roséguld",
    "sage": "Salvia", "sierra_blue": "Sierrablå", "silver": "Silver", "sky_blue": "Himmelsblå",
    "soft_pink": "Ljusrosa", "space_black": "Rymdsvart", "space_grey": "Rymdgrå",
    "starlight": "Stjärnglans", "teal": "Mörkturkos", "ultramarine": "Ultramarin",
    "white": "Vit", "white_titanium": "Vitt titan", "yellow": "Gul",
}

COLOR_KEY_ALIASES = {
    "black": "black", "svart": "black", "white": "white", "vit": "white",
    "silver": "silver", "silverfargad": "silver", "blue": "blue", "bla": "blue", "blue 2": "blue",
    "green": "green", "gron": "green", "pink": "pink", "rosa": "pink",
    "purple": "purple", "lila": "purple", "yellow": "yellow", "gul": "yellow",
    "red": "red", "rod": "red", "product red": "red", "gold": "gold", "guld": "gold",
    "graphite": "graphite", "grafit": "graphite", "grey": "space_grey", "gray": "space_grey", "gra": "space_grey",
    "space grey": "space_grey", "space gray": "space_grey", "rymdgra": "space_grey",
    "space black": "space_black", "rymdsvart": "space_black", "midnight": "midnight", "midnatt": "midnight",
    "starlight": "starlight", "stjarnglans": "starlight", "coral": "coral", "korall": "coral",
    "jet black": "jet_black", "jetsvart": "jet_black", "rose gold": "rose_gold", "roseguld": "rose_gold",
    "lavender": "lavender", "lavendel": "lavender", "sage": "sage", "salvia": "sage",
    "teal": "teal", "morkturkos": "teal", "ultramarine": "ultramarine", "ultramarin": "ultramarine",
    "sierra blue": "sierra_blue", "sierrabla": "sierra_blue", "pacific blue": "pacific_blue",
    "stillahavsbla": "pacific_blue", "havsbla": "pacific_blue", "alpine green": "alpine_green",
    "alpingron": "alpine_green", "midnight green": "midnight_green", "midnattsgron": "midnight_green",
    "mork gron": "midnight_green",
    "deep purple": "deep_purple", "djupbla": "deep_blue", "deep blue": "deep_blue",
    "cosmic orange": "cosmic_orange", "kosmisk orange": "cosmic_orange", "kosmiskt orange": "cosmic_orange",
    "mist blue": "mist_blue", "dimbla": "mist_blue", "disbla": "mist_blue", "sky blue": "sky_blue",
    "himmelsbla": "sky_blue", "soft pink": "soft_pink", "ljusrosa": "soft_pink",
    "cloud white": "cloud_white", "molnvit": "cloud_white", "light gold": "light_gold",
    "ljust guld": "light_gold", "black titanium": "black_titanium", "svart titanium": "black_titanium",
    "svart titan": "black_titanium", "white titanium": "white_titanium", "vit titanium": "white_titanium",
    "vit titan": "white_titanium", "vitt titan": "white_titanium", "blue titanium": "blue_titanium",
    "bla titanium": "blue_titanium", "blatt titan": "blue_titanium",
    "natural titanium": "natural_titanium", "natural titan": "natural_titanium", "titanium": "natural_titanium",
    "naturlig titanium": "natural_titanium", "naturlig titan": "natural_titanium", "naturligt titan": "natural_titanium",
    "desert titanium": "desert_titanium", "sandfargad titanium": "desert_titanium",
    "sandfargat titan": "desert_titanium", "okentitan": "desert_titanium", "orange": "cosmic_orange",
}

COLOR_FAMILIES = {
    "black": {"black", "space_black", "midnight", "jet_black", "black_titanium", "graphite", "space_grey"},
    "white": {"white", "cloud_white", "starlight", "silver", "white_titanium"},
    "blue": {"blue", "blue_titanium", "deep_blue", "mist_blue", "sky_blue", "sierra_blue", "pacific_blue", "ultramarine"},
    "green": {"green", "sage", "alpine_green", "midnight_green", "teal"},
    "purple": {"purple", "deep_purple", "lavender"},
    "pink": {"pink", "soft_pink", "rose_gold"},
    "gold": {"gold", "light_gold", "desert_titanium", "natural_titanium"},
}


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


def _color_key(raw_color: Any) -> str | None:
    color = _clean_text(raw_color)
    if not color:
        return None
    color = re.sub(r"^\|\s*", "", color)
    color = re.split(r"\s*(?:,|-)?\s*(?:grade\s+[a-d]|batteri|som ny)\b", color, maxsplit=1, flags=re.I)[0]
    color = color.strip(" ,|")
    if not color:
        return None
    normalized = color.lower()
    normalized = normalized.replace("å", "a").replace("ä", "a").replace("ö", "o").replace("é", "e")
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized).strip()
    if "natural" in normalized or "naturlig" in normalized or "naturligt" in normalized:
        return "natural_titanium"
    return COLOR_KEY_ALIASES.get(normalized)


def normalize_color(raw_color: Any, model: str | None = None) -> str | None:
    key = _color_key(raw_color)
    if not key:
        return None if model in MODEL_COLOR_KEYS else _clean_text(raw_color)

    allowed = MODEL_COLOR_KEYS.get(model or "")
    if allowed and key not in allowed:
        family = next((members for members in COLOR_FAMILIES.values() if key in members), None)
        family_matches = [candidate for candidate in allowed if family and candidate in family]
        if len(family_matches) == 1:
            key = family_matches[0]

    if allowed and key not in allowed:
        return None
    return COLOR_LABEL_BY_KEY.get(key)


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


def resolve_battery_health(
    retailer: str,
    battery_type: str | None,
    condition: str | None,
    explicit_health: str | None,
) -> tuple[str | None, str, str]:
    """Return battery percentage, semantics and provenance.

    Retailer-wide guarantees are minimums, not measurements of an individual
    device. Only percentages supplied for a specific variant are marked exact.
    """
    if explicit_health:
        return explicit_health, "exact", "retailer_variant"

    retailer_key = retailer.lower()
    battery_key = (battery_type or "").lower()
    condition_key = (condition or "").lower()

    if retailer_key == "swappie":
        # Swappie's API uses Premium for the new-battery option and Prime for
        # the >=95% battery used by its Premium Series. Standard is >=86%.
        if "premium" in battery_key or "nytt" in battery_key:
            return "100%", "exact", "retailer_battery_option"
        if "prime" in battery_key or "plus" in battery_key:
            return "95%", "minimum", "retailer_battery_option"
        return "86%", "minimum", "retailer_guarantee"

    if retailer_key == "phonehero":
        if "nytt" in battery_key:
            return "100%", "exact", "retailer_battery_option"
        return "85%", "minimum", "retailer_guarantee"

    if retailer_key == "fixmyphone":
        return "85%", "minimum", "retailer_guarantee"

    if retailer_key == "happyphone":
        # HappyPhone currently publishes both 80% and 85% on the same product
        # pages. Use the lower explicit guarantee until their copy is coherent.
        return "80%", "minimum", "retailer_guarantee"

    if retailer_key == "renewed":
        if "premium" in condition_key or "helt ny" in condition_key:
            return "100%", "exact", "retailer_condition_policy"
        return "80%", "minimum", "retailer_guarantee"

    return None, "unknown", "not_published"


def infer_battery_health(
    retailer: str,
    battery_type: str | None,
    explicit_health: str | None,
    condition: str | None = None,
) -> str | None:
    """Backward-compatible percentage-only helper."""
    return resolve_battery_health(retailer, battery_type, condition, explicit_health)[0]


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
    if retailer in EXCLUDED_RETAILERS:
        return None
    if stock is not None and stock <= 0:
        return None
    if not is_valid_storage_for_model(model, storage_gb):
        return None

    condition_raw = _clean_text(row.get("condition_grade"))
    condition_tier = normalize_condition_tier(condition_raw)
    condition_mapping = map_used_phone_condition(retailer, condition_raw)
    battery_type = _clean_text(row.get("battery_type"))
    battery_health, battery_health_kind, battery_health_source = resolve_battery_health(
        retailer,
        battery_type,
        condition_raw,
        extract_battery_health(row.get("battery_health"), row.get("color"), row.get("condition_grade")),
    )
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
        "color": normalize_color(row.get("color"), model),
        "condition_raw": condition_raw,
        "condition_tier": condition_tier,
        "condition_label": condition_mapping.condition_label,
        "condition_class": condition_mapping.condition_class,
        "condition_rank": condition_mapping.condition_rank,
        "condition_mapping_confidence": condition_mapping.confidence,
        "condition_source_note": condition_mapping.source_note,
        "legacy_condition_label": CONDITION_LABEL_BY_TIER[condition_tier],
        "battery_type": battery_type,
        "battery_health": battery_health,
        "battery_health_kind": battery_health_kind,
        "battery_health_source": battery_health_source,
        "has_new_battery": bool(
            battery_health == "100%"
            and battery_health_source in {"retailer_battery_option", "retailer_condition_policy"}
        ),
        "price_sek": price_sek,
        "reference_price_sek": reference_price_sek,
        "currency": _clean_text(row.get("currency")) or "SEK",
        "stock": stock if stock is not None else 1,
        "inventory_verified": bool(row.get("inventory_verified")),
        "retailer_variant_id": _clean_text(row.get("variant_id") or row.get("variation_id")),
        "variant_deep_link": bool(row.get("variant_deep_link")),
        "variant_selection_required": bool(row.get("variant_selection_required")),
        "variant_url_kind": _clean_text(row.get("variant_url_kind")),
        "lead_url": url,
        "image_url": _clean_text(row.get("image_url")),
        "scraped_at": _clean_text(row.get("scraped_at")),
        "source_file": source_file.name,
    }


def load_offers(
    input_dir: Path,
    excluded_retailers: set[str] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    offers_by_id: dict[str, dict[str, Any]] = {}
    source_files: list[dict[str, Any]] = []
    excluded = excluded_retailers or set()

    for path in sorted(input_dir.glob(INPUT_GLOB)):
        if path.name.startswith("used_phone_catalog_"):
            continue
        rows = json.loads(path.read_text())
        source_retailer = path.name.removesuffix("_storefront_latest.json")
        source_metadata: dict[str, Any] = {"file": path.name, "rows": len(rows)}
        failure_marker = path.with_suffix(".failed.json")
        refresh_failed = (
            failure_marker.exists()
            and failure_marker.stat().st_mtime >= path.stat().st_mtime
        )
        if refresh_failed:
            source_metadata["excluded"] = "latest refresh failed"
            source_files.append(source_metadata)
            continue
        if source_retailer in excluded:
            source_metadata["excluded"] = "latest refresh failed"
            source_files.append(source_metadata)
            continue
        source_files.append(source_metadata)
        for row in rows:
            offer = normalize_offer(row, path)
            if not offer or offer["retailer"] in excluded:
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
                "condition_classes": sorted(
                    {offer["condition_class"] for offer in model_offers},
                    key=lambda value: CONDITION_CLASSES[value]["rank"],
                    reverse=True,
                ),
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
        "condition_classes": [
            {"value": condition_class, "label": config["label"], "rank": config["rank"]}
            for condition_class, config in sorted(
                CONDITION_CLASSES.items(),
                key=lambda item: item[1]["rank"],
                reverse=True,
            )
            if condition_class != "unknown" and any(offer["condition_class"] == condition_class for offer in offers)
        ],
        "condition_tiers": [
            {"value": tier, "label": label}
            for tier, label in CONDITION_LABEL_BY_TIER.items()
            if any(offer["condition_tier"] == tier for offer in offers)
        ],
    }


def validate_variant_links(offers: list[dict[str, Any]]) -> None:
    ambiguous = [
        offer
        for offer in offers
        if not offer.get("variant_deep_link")
        and not offer.get("variant_selection_required")
    ]
    if ambiguous:
        sample = ", ".join(offer["id"] for offer in ambiguous[:5])
        raise RuntimeError(
            "Used-phone offers have neither an exact variant URL nor a selection warning: "
            f"{len(ambiguous)} offer(s) ({sample})"
        )

    offers_by_url: dict[str, list[dict[str, Any]]] = {}
    for offer in offers:
        offers_by_url.setdefault(offer["lead_url"], []).append(offer)

    misleading_shared_urls = [
        url
        for url, url_offers in offers_by_url.items()
        if len(url_offers) > 1
        and any(
            offer.get("variant_deep_link") or not offer.get("variant_selection_required")
            for offer in url_offers
        )
    ]
    if misleading_shared_urls:
        raise RuntimeError(
            "Variant-specific offers unexpectedly share an outbound URL: "
            + ", ".join(misleading_shared_urls[:5])
        )


def write_json_catalog(output_dir: Path, offers: list[dict[str, Any]], source_files: list[dict[str, Any]]) -> Path:
    validate_variant_links(offers)
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
        "condition_class",
        "condition_rank",
        "condition_mapping_confidence",
        "condition_source_note",
        "legacy_condition_label",
        "battery_type",
        "battery_health",
        "battery_health_kind",
        "battery_health_source",
        "has_new_battery",
        "price_sek",
        "reference_price_sek",
        "currency",
        "stock",
        "inventory_verified",
        "retailer_variant_id",
        "variant_deep_link",
        "variant_selection_required",
        "variant_url_kind",
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


def build_condition_audit(offers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    audit: dict[tuple[str, str | None, str, str], int] = {}
    for offer in offers:
        key = (
            offer["retailer"],
            offer.get("condition_raw"),
            offer["condition_class"],
            offer["condition_mapping_confidence"],
        )
        audit[key] = audit.get(key, 0) + 1

    return [
        {
            "retailer": retailer,
            "condition_raw": condition_raw,
            "condition_class": condition_class,
            "confidence": confidence,
            "offers": count,
        }
        for (retailer, condition_raw, condition_class, confidence), count in sorted(
            audit.items(),
            key=lambda item: (item[0][0], CONDITION_CLASSES[item[0][2]]["rank"] * -1, str(item[0][1])),
        )
    ]


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
    flagged = [
        row
        for row in build_condition_audit(offers)
        if row["condition_class"] == "unknown" or row["confidence"] != "high"
    ]
    if flagged:
        print("Condition mappings to review:")
        for row in flagged:
            print(
                "  {retailer}: {condition_raw!r} -> {condition_class} "
                "({confidence}, {offers} offers)".format(**row)
            )


if __name__ == "__main__":
    main()
