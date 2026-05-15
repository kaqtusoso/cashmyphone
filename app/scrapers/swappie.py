"""
Swappie-scraper – Playwright + direkt REST API.

Swappie's API är skyddat av Cloudflare som blockerar datacenter-IP:er.
Lösning: Playwright startar en riktig headless Chrome, navigerar till Swappies
sida för att lösa Cloudflare JS-challenge och hämta cf_clearance-cookies,
sedan görs API-anropen via samma browser-context (med rätt cookies + TLS).

Swappie exponerar ett öppet API som returnerar inköpspriser för alla kombinationer
av visuellt skick (5 nivåer) och funktionella fel (16 kombinationer = 2^4 flaggor).
Totalt 80 rader per modell + lagring.

─── Condition-nyckelformat (lagras i condition-kolumnen) ─────────────────────
Utan funktionella fel:  "LIKE_NEW"
Med funktionella fel:   "LIKE_NEW:B,BAT,BG,BS"   (alfabetisk ordning)

Funktionskoder:
  B   = BROKEN        – startar ej (Nej på funktionskontroll)
  BAT = BATTERY_ISSUE – batterihälsa under 86%
  BG  = BROKEN_GLASS  – flisor eller kraftiga repor på skärmglas
  BS  = BROKEN_SCREEN – skärmen fungerar ej (fläckar, pixlar, linjer)

─── visual_condition — mappning från Swappies formulär ───────────────────────
visual_condition bestäms av det SÄMSTA svaret bland tre ytor:
  skärmens skick (steg 7) + sidornas skick (steg 8) + baksidans skick (steg 9)

  Formuläralternativ          → API visual_condition
  ─────────────────────────────────────────────────
  "Inga tecken på användning" → LIKE_NEW
  "Minimalt slitage"          → LIKE_NEW
  "Vissa tecken på slitage"   → ALMOST_NEW
  "Synligt slitage"           → GOOD
  "Sprucken eller trasig"     → MODERATE

  SEALED_BOX förekommer i API:et men är inte ett formuläralternativ
  (avser fabriksförseglat skick).

Verifierat: iPhone 17 256GB, baksida "Vissa tecken" (→ ALMOST_NEW) +
85% batteri (→ BAT) = ALMOST_NEW:BAT = 6 138 kr ✓ (Swappie.se 2026-05-14)

─── Batterihälsa ─────────────────────────────────────────────────────────────
Swappie triggar BATTERY_ISSUE när batterihälsan understiger BATTERY_THRESHOLD.
Gränsen är 86% (verifierat: 85% triggar BAT, 90% triggar inte).

För att slå upp rätt pris på CashMyPhone.se:
  battery_health >= 86 → condition-nyckel utan BAT
  battery_health <  86 → lägg till BAT i condition-nyckelns funktionsdel

─── Pris ─────────────────────────────────────────────────────────────────────
  price       – Swappies bud efter besiktning
  limit_price – garanterat golvpris (utbetalas oavsett tillstånd)
  effective   = max(price, limit_price) – detta är vad vi lagrar

─── API-URL ──────────────────────────────────────────────────────────────────
https://swappie.com/api/sell/api/v3/prices/?model_name={model}&country=SE&storages={json_list}
"""
import asyncio
import json
import logging
import re
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from playwright.async_api import async_playwright

from .base import BaseScraper

logger = logging.getLogger(__name__)

API_BASE = "https://swappie.com/api/sell/api/v3/prices/"
COUNTRY = "SE"

# Procent under vilket BATTERY_ISSUE triggas (verifierat: 85% = BAT, 90% = ingen flagga)
BATTERY_THRESHOLD = 86

# Alla lagringsalternativ Swappie stödjer (irrelevanta storlekar ger tomma resultat)
ALL_STORAGES = ["64GB", "128GB", "256GB", "512GB", "1TB"]

# Förkortningar för funktionella fel i condition-nyckeln
FUNC_ABBREV: Dict[str, str] = {
    "BROKEN":        "B",
    "BATTERY_ISSUE": "BAT",
    "BROKEN_GLASS":  "BG",
    "BROKEN_SCREEN": "BS",
}

# Alla iPhones Swappie tar emot (Swappies namnformat)
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

SELL_URL = "https://swappie.com/se/salj-din-iphone/"


def _condition_key(visual: str, functional: List[str]) -> str:
    """
    Bygg en kompakt, sorterbar condition-nyckel.

    Exempel:
      ("LIKE_NEW", [])                              → "LIKE_NEW"
      ("GOOD", ["BROKEN_SCREEN", "BATTERY_ISSUE"])  → "GOOD:BAT,BS"
    """
    if not functional:
        return visual
    abbrevs = sorted(FUNC_ABBREV[f] for f in functional if f in FUNC_ABBREV)
    return f"{visual}:{','.join(abbrevs)}"


def _parse_storage_gb(model_name: str) -> Optional[int]:
    """'iPhone 16 256GB' → 256, 'iPhone 16 1TB' → 1024."""
    m = re.search(r"(\d+)\s*(GB|TB)$", model_name, re.I)
    if not m:
        return None
    val, unit = int(m.group(1)), m.group(2).upper()
    return val * 1024 if unit == "TB" else val


def _clean_model(model_name: str) -> str:
    """'iPhone 16 256GB' → 'iPhone 16'."""
    return re.sub(r"\s+\d+\s*(GB|TB)$", "", model_name, flags=re.I).strip()


async def _fetch_all_models_playwright() -> List[Dict]:
    """
    Startar headless Chrome via Playwright, löser Cloudflare JS-challenge på
    Swappies säljsida och hämtar sedan alla modeller via samma browser-context.
    """
    all_results: List[Dict] = []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"],
        )
        context = await browser.new_context(
            locale="sv-SE",
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/130.0.0.0 Safari/537.36"
            ),
        )

        # Navigera till säljsidan — löser Cloudflare JS-challenge och sätter cf_clearance
        page = await context.new_page()
        try:
            await page.goto(SELL_URL, wait_until="domcontentloaded", timeout=30_000)
            await page.wait_for_timeout(3_000)  # Vänta på CF-challenge
        except Exception as e:
            logger.warning(f"Swappie: kunde inte ladda säljsidan: {e}")
            await browser.close()
            return []

        # Hämta alla modeller via context.request (bär med CF-cookies)
        storages_param = json.dumps(ALL_STORAGES)
        sem = asyncio.Semaphore(3)

        async def fetch_one(model_name: str) -> List[Dict]:
            async with sem:
                url = (
                    f"{API_BASE}"
                    f"?model_name={quote(model_name)}"
                    f"&country={COUNTRY}"
                    f"&storages={quote(storages_param)}"
                )
                try:
                    resp = await context.request.get(
                        url,
                        headers={
                            "Accept": "application/json",
                            "Referer": SELL_URL,
                        },
                        timeout=15_000,
                    )
                    if resp.status != 200:
                        logger.debug(f"Swappie: {model_name} → HTTP {resp.status}")
                        return []
                    data = await resp.json()
                    return data.get("results", [])
                except Exception as e:
                    logger.debug(f"Swappie: fel för {model_name}: {e}")
                    return []
                finally:
                    await asyncio.sleep(0.3)

        raw = await asyncio.gather(*[fetch_one(m) for m in IPHONE_MODELS])
        for results in raw:
            all_results.extend(results)

        await browser.close()

    return all_results


def _parse_results(results: List[Dict]) -> List[Dict]:
    """
    Omvandla rå API-data till prisposter.

    Returnerar en post per unik kombination av (model, storage, condition_key).
    Priset som lagras är max(price, limit_price) – det faktiska utbetalade beloppet.
    """
    prices = []

    for r in results:
        visual = r.get("visual_condition", "")
        if not visual:
            continue

        functional: List[str] = r.get("functional_condition", [])

        raw_model = r.get("model_name", "")
        storage_gb = _parse_storage_gb(raw_model)
        clean_model = _clean_model(raw_model)

        price_data = r.get("price", {})
        try:
            offered = float(price_data.get("price", 0))
            floor = float(price_data.get("limit_price", 0))
        except (ValueError, TypeError):
            continue

        effective = max(offered, floor)
        if effective < 1:
            continue

        condition = _condition_key(visual, functional)

        prices.append({
            "model":      clean_model,
            "storage_gb": storage_gb,
            "condition":  condition,
            "price_sek":  round(effective),
            "url":        SELL_URL,
        })

    return prices


class SwappieScraper(BaseScraper):
    retailer_id = "swappie"
    retailer_name = "Swappie"

    async def fetch_prices(self) -> List[Dict[str, Any]]:
        logger.info(f"Swappie: startar Playwright för {len(IPHONE_MODELS)} modeller...")

        raw_results = await _fetch_all_models_playwright()

        prices = _parse_results(raw_results)
        found_models = len({p["model"] for p in prices})

        logger.info(
            f"Swappie: {len(prices)} priser "
            f"({found_models} modeller, ~{len(prices) // max(found_models, 1)} kombiner/modell)"
        )
        return prices
