"""
FixPhonePro-scraper.

FixPhonePro lagrar sin salj-kalkyl direkt i inline-JS pa /salj/.
Vi extraherar MODELLER-listan och reproducerar deras calculatePrice():

  pris = basePrice * lagringsfaktor * skickfaktorer
  pris = max(100, pris)
  visat pris = Math.round(pris)

Condition-nycklarna ar kompakta for att rymmas i DB:
  s=n|b=n|d=no|f=y|bt=ok
"""
import itertools
import logging
import re
from typing import Any, Dict, List, Optional

import httpx

from .base import BaseScraper
from ..config import settings

logger = logging.getLogger(__name__)

SELL_URL = "https://fixphonepro.net/salj/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "sv-SE,sv;q=0.9,en;q=0.8",
}

MODEL_BLOCK_RE = re.compile(r"\{\s*brand:\s*[\"'](?P<brand>[^\"']+)[\"'][\s\S]*?\n\s*\}", re.M)
NAME_RE = re.compile(r"name:\s*[\"'](?P<name>[^\"']+)[\"']")
STORAGE_RE = re.compile(r"storage:\s*\[(?P<items>[^\]]+)\]", re.S)
BASE_PRICE_RE = re.compile(r"basePrice:\s*(?P<price>\d+)")
STORAGE_VALUE_RE = re.compile(r"[\"'](?P<value>[^\"']+)[\"']")
STORAGE_GB_RE = re.compile(r"(\d+)\s*(GB|TB)", re.I)

STORAGE_FACTORS = {
    16: 0.8,
    32: 0.85,
    64: 0.9,
    128: 1.0,
    256: 1.1,
    512: 1.2,
    1024: 1.3,
}

SCREEN_FACTORS = {
    "n": 1.0,    # Nyskick
    "ns": 0.9,  # Normalt sliten
    "ms": 0.7,  # Mycket sliten
    "sp": 0.4,  # Sprackt
}

BODY_FACTORS = {
    "n": 1.0,
    "ns": 0.95,
    "ms": 0.8,
    "sp": 0.6,
}

DEFECT_FACTORS = {
    "no": 1.0,   # Inget fel
    "yes": 0.7,  # Valfritt fel: Face-ID, ljud, kamera, startar ej, annat
}

FUNCTIONAL_FACTORS = {
    "y": 1.0,
    "n": 0.5,
}

BATTERY_FACTORS = {
    "ok": 1.0,
    "low": 0.9,
}


def _clean_model(name: str) -> str:
    name = re.sub(r"\s+", " ", name or "").strip()
    name = name.replace("iPhone 17 Pro max", "iPhone 17 Pro Max")
    name = name.replace("iPhone SE 2020", "iPhone SE (2020)")
    name = name.replace("iPhone SE 2022", "iPhone SE (2022)")
    return name


def _parse_storage(value: str) -> Optional[int]:
    match = STORAGE_GB_RE.search(value or "")
    if not match:
        return None
    amount = int(match.group(1))
    return amount * 1024 if match.group(2).upper() == "TB" else amount


def _condition_key(screen: str, body: str, defect: str, functional: str, battery: str) -> str:
    return f"s={screen}|b={body}|d={defect}|f={functional}|bt={battery}"


def _calculate_price(base_price: int, storage_gb: int, screen: str, body: str, defect: str, functional: str, battery: str) -> int:
    price = float(base_price)
    price *= STORAGE_FACTORS.get(storage_gb, 1.0)
    price *= SCREEN_FACTORS[screen]
    price *= BODY_FACTORS[body]
    price *= DEFECT_FACTORS[defect]
    price *= FUNCTIONAL_FACTORS[functional]
    price *= BATTERY_FACTORS[battery]
    return round(max(100, price))


def _extract_models(html: str) -> List[Dict[str, Any]]:
    models: List[Dict[str, Any]] = []
    for match in MODEL_BLOCK_RE.finditer(html):
        block = match.group(0)
        if match.group("brand") != "Apple":
            continue

        name_match = NAME_RE.search(block)
        storage_match = STORAGE_RE.search(block)
        price_match = BASE_PRICE_RE.search(block)
        if not name_match or not storage_match or not price_match:
            continue

        model_name = _clean_model(name_match.group("name"))
        if not model_name.startswith("iPhone"):
            continue

        storages = [
            storage_gb
            for storage_gb in (_parse_storage(m.group("value")) for m in STORAGE_VALUE_RE.finditer(storage_match.group("items")))
            if storage_gb
        ]
        if not storages:
            continue

        models.append({
            "model": model_name,
            "storages": storages,
            "base_price": int(price_match.group("price")),
        })

    return models


class FixPhoneProScraper(BaseScraper):
    retailer_id = "fixphonepro"
    retailer_name = "FixPhonePro"
    min_models = 20
    min_rows = 5000
    expected_conditions = frozenset(
        _condition_key(screen, body, defect, functional, battery)
        for screen, body, defect, functional, battery in itertools.product(
            SCREEN_FACTORS, BODY_FACTORS, DEFECT_FACTORS,
            FUNCTIONAL_FACTORS, BATTERY_FACTORS,
        )
    )

    async def fetch_prices(self) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(
            timeout=settings.request_timeout_seconds,
            follow_redirects=True,
            headers=HEADERS,
        ) as client:
            resp = await client.get(SELL_URL)
            resp.raise_for_status()

        models = _extract_models(resp.text)
        prices: List[Dict[str, Any]] = []

        for model in models:
            for storage_gb in model["storages"]:
                for screen, body, defect, functional, battery in itertools.product(
                    SCREEN_FACTORS.keys(),
                    BODY_FACTORS.keys(),
                    DEFECT_FACTORS.keys(),
                    FUNCTIONAL_FACTORS.keys(),
                    BATTERY_FACTORS.keys(),
                ):
                    prices.append({
                        "model": model["model"],
                        "storage_gb": storage_gb,
                        "condition": _condition_key(screen, body, defect, functional, battery),
                        "price_sek": _calculate_price(
                            model["base_price"],
                            storage_gb,
                            screen,
                            body,
                            defect,
                            functional,
                            battery,
                        ),
                        "url": SELL_URL,
                    })

        logger.info(f"FixPhonePro: {len(prices)} priser")
        return prices
