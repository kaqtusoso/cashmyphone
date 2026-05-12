"""
Swappie-scraper – cloudscraper + direkt REST API.

Swappie har ett öppet API på /api/sell/api/v3/prices/ som returnerar
inköpspriser för alla kombinationer av visuellt skick och funktionella fel.
cloudscraper hanterar Cloudflare-skyddet utan Playwright.

API-struktur per resultat:
  - model_name: "iPhone 16 256GB"
  - visual_condition: SEALED_BOX | LIKE_NEW | ALMOST_NEW | GOOD | MODERATE
  - functional_condition: [] | [BROKEN] | [BROKEN_SCREEN] | [BATTERY_ISSUE] | kombinationer
  - price.price: faktiskt bud (SEK)
  - price.limit_price: garanterat minimum (golvpris)

Vi lagrar 5 skicksnivåer per modell/lagring (perfekt skick, inga funktionsfel).
"""
import asyncio
import logging
import json
from typing import List, Dict, Any, Optional
from urllib.parse import quote
from .base import BaseScraper

logger = logging.getLogger(__name__)

API_BASE = "https://swappie.com/api/sell/api/v3/prices/"
ALL_STORAGES = ["64GB", "128GB", "256GB", "512GB", "1TB"]

# Modeller att hämta (Swappies namnformat)
IPHONE_MODELS = [
    "iPhone 17 Pro Max", "iPhone 17 Pro", "iPhone 17 Plus", "iPhone 17",
    "iPhone 16 Pro Max", "iPhone 16 Pro", "iPhone 16 Plus", "iPhone 16",
    "iPhone 15 Pro Max", "iPhone 15 Pro", "iPhone 15 Plus", "iPhone 15",
    "iPhone 14 Pro Max", "iPhone 14 Pro", "iPhone 14 Plus", "iPhone 14",
    "iPhone 13 Pro Max", "iPhone 13 Pro", "iPhone 13 mini", "iPhone 13",
    "iPhone 12 Pro Max", "iPhone 12 Pro", "iPhone 12 mini", "iPhone 12",
    "iPhone 11 Pro Max", "iPhone 11 Pro", "iPhone 11",
    "iPhone SE (3rd generation)", "iPhone SE (2nd generation)",
    "iPhone XS Max", "iPhone XS", "iPhone XR",
]

# Mappar visual_condition till vårt skick-fält
VISUAL_TO_CONDITION = {
    "SEALED_BOX": "sealed_box",
    "LIKE_NEW":   "like_new",
    "ALMOST_NEW": "almost_new",
    "GOOD":       "good",
    "MODERATE":   "moderate",
}

# Visuella skick vi lagrar (bara "perfekt skick" = inga funktionsfel)
STORE_VISUAL = set(VISUAL_TO_CONDITION.keys())


def _fetch_model_sync(model_name: str) -> List[Dict]:
    """Synkront API-anrop via cloudscraper (körs i threadpool)."""
    try:
        import cloudscraper
    except ImportError:
        raise RuntimeError("cloudscraper saknas – installera: pip install cloudscraper")

    storages_param = json.dumps(ALL_STORAGES)
    url = f"{API_BASE}?model_name={quote(model_name)}&country=SE&storages={quote(storages_param)}"

    scraper = cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "linux", "mobile": False}
    )
    resp = scraper.get(url, timeout=20)

    if resp.status_code != 200:
        logger.debug(f"Swappie: {model_name} → HTTP {resp.status_code}")
        return []

    data = resp.json()
    results = data.get("results", [])
    return results


def _parse_results(results: List[Dict], model_name: str) -> List[Dict]:
    """Extrahera priser per visuellt skick (inga funktionsfel)."""
    prices = []
    url = "https://swappie.com/se/salj-din-iphone/"

    for r in results:
        # Bara rader utan funktionsfel
        if r.get("functional_condition"):
            continue

        visual = r.get("visual_condition", "")
        condition = VISUAL_TO_CONDITION.get(visual)
        if not condition:
            continue

        # Extrahera lagring från model_name, t.ex. "iPhone 16 256GB" → 256
        raw_model = r.get("model_name", "")
        storage_gb = _parse_storage(raw_model)

        price_val = r.get("price", {}).get("price", 0)
        try:
            price = int(price_val)
        except (ValueError, TypeError):
            continue

        if price < 100:
            continue

        # Rensa modellnamnet (ta bort lagring från slutet)
        clean_model = _clean_model_name(raw_model)

        prices.append({
            "model": clean_model,
            "storage_gb": storage_gb,
            "condition": condition,
            "price_sek": price,
            "url": url,
        })

    return prices


def _parse_storage(model_name: str) -> Optional[int]:
    """'iPhone 16 256GB' → 256, 'iPhone 16 1TB' → 1024."""
    import re
    m = re.search(r"(\d+)\s*(GB|TB)$", model_name, re.I)
    if not m:
        return None
    val, unit = int(m.group(1)), m.group(2).upper()
    return val * 1024 if unit == "TB" else val


def _clean_model_name(model_name: str) -> str:
    """'iPhone 16 256GB' → 'iPhone 16'."""
    import re
    return re.sub(r"\s+\d+\s*(GB|TB)$", "", model_name, flags=re.I).strip()


class SwappieScraper(BaseScraper):
    retailer_id = "swappie"
    retailer_name = "Swappie"

    async def fetch_prices(self) -> List[Dict[str, Any]]:
        logger.info(f"Swappie: hämtar {len(IPHONE_MODELS)} modeller parallellt...")

        # Kör synkrona cloudscraper-anrop parallellt i threadpool
        tasks = [
            asyncio.to_thread(_fetch_model_sync, model)
            for model in IPHONE_MODELS
        ]
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)

        prices = []
        found = 0
        for model_name, result in zip(IPHONE_MODELS, raw_results):
            if isinstance(result, Exception):
                logger.debug(f"Swappie: fel för {model_name}: {result}")
                continue
            if not result:
                continue
            parsed = _parse_results(result, model_name)
            if parsed:
                found += 1
            prices.extend(parsed)

        logger.info(f"Swappie: {len(prices)} priser från {found} modeller")
        return prices
