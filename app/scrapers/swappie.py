"""
Swappie-scraper – curl-cffi + fallback via Playwright.

Swappie's API är skyddat av Cloudflare och är känsligt för datacenter-IP/TLS-
fingerprint. Första valet är därför curl-cffi med Chrome-impersonering, som gör
direkta API-anrop utan att kräva manuell webbsession. Om det slutar ge resultat
faller scrapern tillbaka till Playwright och fetch inne i browser-context.

Swappie exponerar ett öppet API som returnerar inköpspriser för alla kombinationer
av visuellt skick och funktionella flaggor. API:t innehåller även BROKEN-rader,
trots att det svenska säljflödet stoppar telefoner som inte klarar
funktionskollen. De raderna filtreras därför bort innan import.

─── Condition-nyckelformat (lagras i condition-kolumnen) ─────────────────────
Utan funktionella fel:  "LIKE_NEW"
Med tillåtna skickfel:  "LIKE_NEW:BAT,BG,BS"   (alfabetisk ordning)

Funktionskoder:
  B   = BROKEN        – underkänd funktionskoll (filtreras alltid bort)
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

from curl_cffi.requests import AsyncSession as CurlAsyncSession
from playwright.async_api import async_playwright

from .base import BaseScraper

logger = logging.getLogger(__name__)

API_BASE = "https://swappie.com/api/sell/api/v3/prices/"
COUNTRY = "SE"

# Procent under vilket BATTERY_ISSUE triggas (verifierat: 85% = BAT, 90% = ingen flagga)
BATTERY_THRESHOLD = 86

# Alla lagringsalternativ Swappie stödjer (irrelevanta storlekar ger tomma resultat)
ALL_STORAGES = ["64GB", "128GB", "256GB", "512GB", "1TB", "2TB"]

# Förkortningar för funktionella fel i condition-nyckeln
FUNC_ABBREV: Dict[str, str] = {
    "BROKEN":        "B",
    "BATTERY_ISSUE": "BAT",
    "BROKEN_GLASS":  "BG",
    "BROKEN_SCREEN": "BS",
}

INELIGIBLE_FUNCTIONAL_CONDITIONS = {"BROKEN"}

# Modellerna som är valbara i Swappies svenska säljflöde. Pris-API:t kan
# fortfarande returnera priser för utgångna modeller, så modellväljaren är
# källan till sanningen. Verifierad 2026-07-21.
IPHONE_MODELS: List[str] = [
    "iPhone 17 Pro Max", "iPhone 17 Pro", "iPhone Air", "iPhone 17", "iPhone 17e",
    "iPhone 16 Pro Max", "iPhone 16 Pro", "iPhone 16 Plus", "iPhone 16e", "iPhone 16",
    "iPhone 15 Pro Max", "iPhone 15 Pro", "iPhone 15 Plus", "iPhone 15",
    "iPhone 14 Pro Max", "iPhone 14 Pro", "iPhone 14 Plus", "iPhone 14",
    "iPhone 13 Pro Max", "iPhone 13 Pro", "iPhone 13", "iPhone 13 mini",
    "iPhone 12 Pro Max", "iPhone 12 Pro", "iPhone 12", "iPhone 12 mini",
    "iPhone SE 2022",
]

SELL_URL = "https://swappie.com/se/salj-din-iphone/"

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "sv-SE,sv;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": SELL_URL,
    "Origin": "https://swappie.com",
    "sec-ch-ua": '"Chromium";v="136", "Google Chrome";v="136", "Not?A_Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
}


def _condition_key(visual: str, functional: List[str]) -> str:
    """
    Bygg en kompakt, sorterbar condition-nyckel.

    Exempel:
      ("LIKE_NEW", [])                              → "LIKE_NEW"
      ("GOOD", ["BROKEN_SCREEN", "BATTERY_ISSUE"])  → "GOOD:BAT,BS"
    """
    abbrevs = sorted(FUNC_ABBREV[f] for f in functional if f in FUNC_ABBREV)
    return f"{visual}:{','.join(abbrevs)}" if abbrevs else visual


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


def _prices_url(model_name: str) -> str:
    storages_param = json.dumps(ALL_STORAGES)
    return (
        f"{API_BASE}"
        f"?model_name={quote(model_name)}"
        f"&country={COUNTRY}"
        f"&storages={quote(storages_param)}"
    )


async def _fetch_model_curl(session: CurlAsyncSession, model_name: str) -> List[Dict]:
    """Hämta en modell direkt med browser-lik TLS via curl-cffi."""
    try:
        resp = await session.get(_prices_url(model_name), headers=HEADERS, timeout=25)
        if resp.status_code != 200:
            logger.debug(f"Swappie curl-cffi: {model_name} → HTTP {resp.status_code}")
            return []
        return resp.json().get("results", [])
    except Exception as e:
        logger.debug(f"Swappie curl-cffi: {model_name}: {e}")
        return []


async def _fetch_all_models_curl() -> List[Dict]:
    """
    Primär väg: direkta API-anrop via curl-cffi.

    Detta undviker att scrapern behöver öppna Swappies sida och hoppas att
    Cloudflare-challengen löses rätt i headless browser.
    """
    all_results: List[Dict] = []

    async with CurlAsyncSession(impersonate="chrome136") as session:
        sem = asyncio.Semaphore(4)

        async def fetch_with_sem(model_name: str) -> List[Dict]:
            async with sem:
                result = await _fetch_model_curl(session, model_name)
                await asyncio.sleep(0.25)
                return result

        results = await asyncio.gather(
            *[fetch_with_sem(model_name) for model_name in IPHONE_MODELS],
            return_exceptions=True,
        )

    for result in results:
        if isinstance(result, list):
            all_results.extend(result)

    return all_results


async def _fetch_all_models_playwright() -> List[Dict]:
    """
    Startar headless Chrome via Playwright, löser Cloudflare JS-challenge på
    Swappies säljsida och hämtar sedan alla modeller via page.evaluate() —
    fetch() körs inne i webbläsarens JS-kontext (rätt cookies, rätt TLS).
    """
    all_results: List[Dict] = []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"],
        )
        page = await browser.new_page()

        # Navigera till säljsidan — löser Cloudflare JS-challenge
        try:
            await page.goto(SELL_URL, wait_until="domcontentloaded", timeout=30_000)
            await page.wait_for_timeout(5_000)  # Vänta tills CF-challenge löst
            title = await page.title()
            logger.info(f"Swappie: page title = {title!r}")
        except Exception as e:
            logger.warning(f"Swappie: navigation misslyckades: {e}")
            await browser.close()
            return []

        for model_name in IPHONE_MODELS:
            url = _prices_url(model_name)
            try:
                data = await page.evaluate(
                    """async (url) => {
                        try {
                            const r = await fetch(url, {
                                headers: { 'Accept': 'application/json' }
                            });
                            if (!r.ok) return null;
                            return await r.json();
                        } catch (e) { return null; }
                    }""",
                    url,
                )
                if data:
                    results = data.get("results", [])
                    all_results.extend(results)
                    logger.debug(f"Swappie: {model_name} → {len(results)} resultat")
            except Exception as e:
                logger.debug(f"Swappie: {model_name}: {e}")
            await asyncio.sleep(0.2)

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

        functional: List[str] = r.get("functional_condition") or []
        if INELIGIBLE_FUNCTIONAL_CONDITIONS.intersection(functional):
            continue

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
        logger.info(f"Swappie: hämtar {len(IPHONE_MODELS)} modeller via curl-cffi...")

        raw_results = await _fetch_all_models_curl()
        if not raw_results:
            logger.warning("Swappie: curl-cffi gav inga resultat – provar Playwright fallback")
            raw_results = await _fetch_all_models_playwright()

        prices = _parse_results(raw_results)
        found_models = len({p["model"] for p in prices})

        logger.info(
            f"Swappie: {len(prices)} priser "
            f"({found_models} modeller, ~{len(prices) // max(found_models, 1)} kombiner/modell)"
        )
        return prices
