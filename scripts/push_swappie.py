#!/usr/bin/env python3
"""
Lokal Swappie-pusher — hämtar priser via curl-cffi (fungerar på hem-IP)
och pushar dem till Railway-databasen via /api/import-prices.

Kör manuellt:
    python scripts/push_swappie.py

Lägg till i crontab för daglig körning kl 06:00:
    0 6 * * * cd /Users/pascalbrjansson/Documents/Claude/Projects/CashMyPhone && python scripts/push_swappie.py >> /tmp/swappie_push.log 2>&1
"""
import asyncio
import json
import logging
import re
import sys
from typing import Dict, List, Optional
from urllib.parse import quote

import httpx
from curl_cffi.requests import AsyncSession

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ─── Konfiguration ────────────────────────────────────────────────────────────
RAILWAY_URL = "https://cashmyphone-production.up.railway.app"
API_KEY     = "banankaka998877665544332211"

API_BASE    = "https://swappie.com/api/sell/api/v3/prices/"
COUNTRY     = "SE"
SELL_URL    = "https://swappie.com/se/salj-din-iphone/"
ALL_STORAGES = ["64GB", "128GB", "256GB", "512GB", "1TB"]
BATTERY_THRESHOLD = 86

FUNC_ABBREV: Dict[str, str] = {
    "BROKEN":        "B",
    "BATTERY_ISSUE": "BAT",
    "BROKEN_GLASS":  "BG",
    "BROKEN_SCREEN": "BS",
}

IPHONE_MODELS: List[str] = [
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

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "sv-SE,sv;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": SELL_URL,
    "Origin": "https://swappie.com",
    "sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
}


# ─── Hjälpfunktioner (samma logik som swappie.py) ────────────────────────────

def _condition_key(visual: str, functional: List[str]) -> str:
    if not functional:
        return visual
    abbrevs = sorted(FUNC_ABBREV[f] for f in functional if f in FUNC_ABBREV)
    return f"{visual}:{','.join(abbrevs)}"


def _parse_storage_gb(model_name: str) -> Optional[int]:
    m = re.search(r"(\d+)\s*(GB|TB)$", model_name, re.I)
    if not m:
        return None
    val, unit = int(m.group(1)), m.group(2).upper()
    return val * 1024 if unit == "TB" else val


def _clean_model(model_name: str) -> str:
    return re.sub(r"\s+\d+\s*(GB|TB)$", "", model_name, flags=re.I).strip()


async def _fetch_model(session: AsyncSession, model_name: str) -> List[Dict]:
    storages_param = json.dumps(ALL_STORAGES)
    url = (
        f"{API_BASE}"
        f"?model_name={quote(model_name)}"
        f"&country={COUNTRY}"
        f"&storages={quote(storages_param)}"
    )
    try:
        resp = await session.get(url, headers=HEADERS, timeout=20)
        if resp.status_code != 200:
            logger.debug(f"  {model_name} → HTTP {resp.status_code}")
            return []
        return resp.json().get("results", [])
    except Exception as e:
        logger.debug(f"  {model_name}: {e}")
        return []


def _parse_results(results: List[Dict]) -> List[Dict]:
    prices = []
    for r in results:
        visual = r.get("visual_condition", "")
        if not visual:
            continue
        functional = r.get("functional_condition", [])
        raw_model  = r.get("model_name", "")
        storage_gb = _parse_storage_gb(raw_model)
        clean      = _clean_model(raw_model)
        price_data = r.get("price", {})
        try:
            offered = float(price_data.get("price", 0))
            floor   = float(price_data.get("limit_price", 0))
        except (ValueError, TypeError):
            continue
        effective = max(offered, floor)
        if effective < 1:
            continue
        prices.append({
            "model":      clean,
            "storage_gb": storage_gb,
            "condition":  _condition_key(visual, functional),
            "price_sek":  round(effective),
            "url":        SELL_URL,
        })
    return prices


# ─── Huvud ────────────────────────────────────────────────────────────────────

async def fetch_swappie_prices() -> List[Dict]:
    logger.info(f"Hämtar {len(IPHONE_MODELS)} modeller via curl-cffi...")

    async with AsyncSession(impersonate="chrome130") as session:
        sem = asyncio.Semaphore(3)

        async def fetch_with_sem(model: str) -> List[Dict]:
            async with sem:
                result = await _fetch_model(session, model)
                await asyncio.sleep(0.4)
                return result

        raw = await asyncio.gather(
            *[fetch_with_sem(m) for m in IPHONE_MODELS],
            return_exceptions=True,
        )

    all_results = []
    for r in raw:
        if isinstance(r, Exception) or not r:
            continue
        all_results.extend(r)

    prices = _parse_results(all_results)
    found_models = len({p["model"] for p in prices})
    logger.info(f"✅ {len(prices)} priser ({found_models} modeller)")
    return prices


async def main():
    logger.info("🚀 Startar lokal Swappie-pusher...")

    prices = await fetch_swappie_prices()

    if not prices:
        logger.warning("Inga priser hämtades — kontrollera din internetanslutning.")
        sys.exit(1)

    logger.info(f"Pushar {len(prices)} priser till Railway...")

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{RAILWAY_URL}/api/import-prices/swappie",
            headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
            content=json.dumps(prices),
        )
        if resp.status_code == 200:
            result = resp.json()
            logger.info(f"🎉 Klart! {result['imported']} priser sparade i Railway-databasen.")
        else:
            logger.error(f"API-fel {resp.status_code}: {resp.text}")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
