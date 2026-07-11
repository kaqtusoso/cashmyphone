from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Literal, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel, ConfigDict, Field


router = APIRouter(prefix="/api/used-phones", tags=["used phones"])

CATALOG_PATH = Path("data/retail_prices/used_phone_catalog_latest.json")


class UsedPhoneOffer(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    id: str
    retailer: str
    retailer_label: str
    sku: str
    model: str
    model_slug: str
    storage_gb: Optional[int] = None
    storage: Optional[str] = None
    color: Optional[str] = None
    condition_raw: Optional[str] = None
    condition_tier: str
    condition_label: str
    condition_class: Optional[str] = None
    condition_rank: Optional[int] = None
    condition_mapping_confidence: Optional[str] = None
    condition_source_note: Optional[str] = None
    legacy_condition_label: Optional[str] = None
    battery_type: Optional[str] = None
    battery_health: Optional[str] = None
    has_new_battery: bool = False
    price_sek: int
    reference_price_sek: Optional[int] = None
    currency: str = "SEK"
    stock: int = 1
    lead_url: str
    image_url: Optional[str] = None
    scraped_at: Optional[str] = None
    source_file: Optional[str] = None


class UsedPhoneModelSummary(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model: str
    model_slug: str
    offer_count: int
    retailer_count: int
    min_price_sek: int
    max_price_sek: int
    storage_options_gb: list[int]
    condition_tiers: list[str]
    condition_classes: list[str] = Field(default_factory=list)
    colors: list[str]


class UsedPhoneListResponse(BaseModel):
    generated_at: Optional[str]
    total_offers: int
    matching_offers: int
    offset: int
    limit: int
    source_files: list[dict[str, Any]]
    filter_options: dict[str, Any]
    models: list[UsedPhoneModelSummary]
    offers: list[UsedPhoneOffer]


class UsedPhoneCatalogResponse(BaseModel):
    generated_at: Optional[str]
    total_offers: int
    source_files: list[dict[str, Any]]
    filter_options: dict[str, Any]
    models: list[UsedPhoneModelSummary]
    offers: list[UsedPhoneOffer]


class UsedPhoneCatalogStatus(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    exists: bool
    generated_at: Optional[str] = None
    total_offers: int = 0
    model_count: int = 0
    source_files: list[dict[str, Any]] = Field(default_factory=list)


def _load_catalog() -> dict[str, Any]:
    if not CATALOG_PATH.exists():
        return {
            "generated_at": None,
            "total_offers": 0,
            "source_files": [],
            "filter_options": {
                "models": [],
                "retailers": [],
                "storage_options_gb": [],
                "condition_classes": [],
                "condition_tiers": [],
            },
            "models": [],
            "offers": [],
        }
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def _parse_battery_percent(value: str | None) -> int | None:
    if not value:
        return None
    match = re.search(r"(\d{2,3})", value)
    if not match:
        return None
    return int(match.group(1))


def _matches_any(value: str | None, allowed: list[str] | None) -> bool:
    if not allowed:
        return True
    if value is None:
        return False
    lowered = value.lower()
    return lowered in {item.lower() for item in allowed}


def _filter_offers(
    offers: list[dict[str, Any]],
    model_slug: str | None,
    model: str | None,
    storage_gb: int | None,
    min_storage_gb: int | None,
    max_price_sek: int | None,
    min_price_sek: int | None,
    condition_tier: list[str] | None,
    retailer: list[str] | None,
    color: str | None,
    has_new_battery: bool | None,
    min_battery_health: int | None,
) -> list[dict[str, Any]]:
    filtered: list[dict[str, Any]] = []
    for offer in offers:
        if model_slug and offer.get("model_slug") != model_slug:
            continue
        if model and model.lower() not in str(offer.get("model", "")).lower():
            continue
        if storage_gb is not None and offer.get("storage_gb") != storage_gb:
            continue
        if min_storage_gb is not None and (offer.get("storage_gb") is None or offer["storage_gb"] < min_storage_gb):
            continue
        if max_price_sek is not None and offer.get("price_sek", 0) > max_price_sek:
            continue
        if min_price_sek is not None and offer.get("price_sek", 0) < min_price_sek:
            continue
        if not _matches_any(offer.get("condition_tier"), condition_tier):
            continue
        if not _matches_any(offer.get("retailer"), retailer):
            continue
        if color and color.lower() not in str(offer.get("color") or "").lower():
            continue
        if has_new_battery is not None and offer.get("has_new_battery") is not has_new_battery:
            continue
        if min_battery_health is not None:
            battery_health = _parse_battery_percent(offer.get("battery_health"))
            if battery_health is None or battery_health < min_battery_health:
                continue
        filtered.append(offer)
    return filtered


def _sort_offers(offers: list[dict[str, Any]], sort: str) -> list[dict[str, Any]]:
    if sort == "price_desc":
        return sorted(offers, key=lambda offer: offer.get("price_sek", 0), reverse=True)
    if sort == "newest":
        return sorted(offers, key=lambda offer: offer.get("scraped_at") or "", reverse=True)
    if sort == "storage_desc":
        return sorted(offers, key=lambda offer: (offer.get("storage_gb") or 0, -offer.get("price_sek", 0)), reverse=True)
    return sorted(offers, key=lambda offer: (offer.get("price_sek", 0), offer.get("retailer_label") or ""))


@router.get("", response_model=UsedPhoneListResponse, summary="Lista begagnade mobiler att köpa")
async def list_used_phones(
    model_slug: Optional[str] = Query(None, description="Exakt modellslug, t.ex. iphone-16"),
    model: Optional[str] = Query(None, description="Fritext på modell, t.ex. iPhone 16"),
    storage_gb: Optional[int] = Query(None, description="Exakt lagring i GB"),
    min_storage_gb: Optional[int] = Query(None, description="Minsta lagring i GB"),
    max_price_sek: Optional[int] = Query(None, description="Högsta pris"),
    min_price_sek: Optional[int] = Query(None, description="Lägsta pris"),
    condition_tier: Optional[list[str]] = Query(None, description="Skicknivå, kan anges flera gånger"),
    retailer: Optional[list[str]] = Query(None, description="Återförsäljare, kan anges flera gånger"),
    color: Optional[str] = Query(None, description="Fritext på färg"),
    has_new_battery: Optional[bool] = Query(None, description="Endast erbjudanden med nytt batteri"),
    min_battery_health: Optional[int] = Query(None, ge=0, le=100, description="Minsta batterihälsa i procent"),
    sort: Literal["price_asc", "price_desc", "newest", "storage_desc"] = Query("price_asc"),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    catalog = _load_catalog()
    filtered = _filter_offers(
        catalog.get("offers", []),
        model_slug=model_slug,
        model=model,
        storage_gb=storage_gb,
        min_storage_gb=min_storage_gb,
        max_price_sek=max_price_sek,
        min_price_sek=min_price_sek,
        condition_tier=condition_tier,
        retailer=retailer,
        color=color,
        has_new_battery=has_new_battery,
        min_battery_health=min_battery_health,
    )
    sorted_offers = _sort_offers(filtered, sort)
    page = sorted_offers[offset : offset + limit]
    return UsedPhoneListResponse(
        generated_at=catalog.get("generated_at"),
        total_offers=catalog.get("total_offers", 0),
        matching_offers=len(filtered),
        offset=offset,
        limit=limit,
        source_files=catalog.get("source_files", []),
        filter_options=catalog.get("filter_options", {}),
        models=catalog.get("models", []),
        offers=page,
    )


@router.get("/catalog", response_model=UsedPhoneCatalogResponse, summary="Hämta hela begagnat-katalogen")
async def get_used_phone_catalog():
    catalog = _load_catalog()
    return UsedPhoneCatalogResponse(
        generated_at=catalog.get("generated_at"),
        total_offers=catalog.get("total_offers", 0),
        source_files=catalog.get("source_files", []),
        filter_options=catalog.get("filter_options", {}),
        models=catalog.get("models", []),
        offers=catalog.get("offers", []),
    )


@router.get("/models", response_model=list[UsedPhoneModelSummary], summary="Lista modeller i begagnat-katalogen")
async def list_used_phone_models():
    catalog = _load_catalog()
    return catalog.get("models", [])


@router.get("/status", response_model=UsedPhoneCatalogStatus, summary="Status för begagnat-katalogen")
async def get_used_phone_catalog_status():
    catalog = _load_catalog()
    return UsedPhoneCatalogStatus(
        exists=CATALOG_PATH.exists(),
        generated_at=catalog.get("generated_at"),
        total_offers=catalog.get("total_offers", 0),
        model_count=len(catalog.get("models", [])),
        source_files=catalog.get("source_files", []),
    )
