"""
HappyPhone-scraper – klientsidig prisberäkning via data-calc JSON.

HappyPhone ägs av FixMyPhone och använder ett identiskt formulärflöde och
prismodell. Alla priser är inbäddade i ett JSON-attribut (data-calc) direkt
i HTML-koden för varje modellsida – inga extra API-anrop behövs.

─── Formulärstruktur (8 steg) ───────────────────────────────────────────────
  Steg 1 – Lagring (storage): 64GB / 128GB / 256GB / 512GB / 1TB
  Steg 2 – Fungerar enheten felfritt? Ja / Nej → isWorking
  Steg 3 – Är skärmen helt felfri? Ja / Nej → isDisplay
  Steg 4 – Visuellt skick: Som ny / Mycket bra / Bra / Okej → condition
  Steg 5 – Är baksidan/kameralinsen trasig? Ja / Nej → isCracked
  Steg 6 – Böjd, fuktskadad eller Face/Touch ID trasig? Ja / Nej → isWaterDamaged
  Steg 7 – Batteri ≥ 85%? Ja / Nej / Jag är inte säker → isBattery (2/1/0)
  Steg 8 – HappyPhone-box? Ja / Nej → hasBox (+200 kr, lagras EJ i DB)

─── data-calc JSON (i .calcContainer) ───────────────────────────────────────
  Identisk struktur med FixMyPhone – se fixmyphone.py för fullständig spec.

─── Prisformel ───────────────────────────────────────────────────────────────
  1. Om böjd/vatten/Face ID (water_damaged): pris = isWaterDamaged (60 kr)
  2. Annars:
       pris = variations[storage_index][condition]
       om ej fungerar:       pris -= ifWorking
       om skärm trasig:      pris -= ifDisplay
       om baksida trasig:    pris -= ifCrackedBack
       om batteri < 85%:     pris -= ifBattery
       pris = max(pris, int(lowest))

─── Condition-nyckel (lagras i condition-kolumnen) ───────────────────────────
  Identisk med FixMyPhone – se fixmyphone.py för fullständig spec.

  Basvillkor:   like_new | very_good | good | acceptable
  :no_back      = baksida/kameralins trasig
  :no_battery   = batteri under 85%
  :no_display   = skärm trasig
  :no_working   = enheten fungerar ej
  water_damaged = alltid 60 kr

─── URL-struktur ─────────────────────────────────────────────────────────────
  Produktsitemap:  https://happyphone.se/product-sitemap1.xml
  Modellsida:      https://happyphone.se/product/{slug}/

  OBS: sitatemap innehåller både säljsidor (har data-calc) och köpsidor
  för begagnade/förnyadeiPhones (saknar data-calc). Köpsidorna filtreras
  automatiskt bort av _parse_model_page när data-calc saknas.
"""
import asyncio
import json
import logging
import re
from itertools import product as iterproduct
from typing import Any, Dict, List, Optional, Tuple

import httpx
from bs4 import BeautifulSoup

from .base import BaseScraper
from ..config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://happyphone.se"
SITEMAP_URL = f"{BASE_URL}/product-sitemap1.xml"
PRODUCT_URL = f"{BASE_URL}/product/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "sv-SE,sv;q=0.9",
}

CONDITIONS = ["like_new", "very_good", "good", "acceptable"]
MIN_PRICE = 1

# Verifierade säljslugar (har data-calc) — används som fallback om sitatemap är otillgänglig.
# OBS: flera modeller har slug-suffix "-2" för säljsidan (köpsidan saknar suffixet).
# Verifierat manuellt 2026-05-15.
FALLBACK_SLUGS: List[str] = [
    "iphone-11-2",                                    # iPhone 11 (iphone-11 = köpsida)
    "iphone-11-pro", "iphone-11-pro-max",
    "iphone-12", "iphone-12-mini", "iphone-12-pro", "iphone-12-pro-max",
    "iphone-13-2",                                    # iPhone 13 (iphone-13 = köpsida)
    "iphone-13-mini", "iphone-13-mini-2",
    "iphone-13-pro-2",                                # iPhone 13 Pro (iphone-13-pro = köpsida)
    "iphone-13-pro-max-2",                            # iPhone 13 Pro Max (iphone-13-pro-max = köpsida)
    "iphone-14", "iphone-14-plus", "iphone-14-pro", "iphone-14-pro-max",
    "iphone-15", "iphone-15-plus", "iphone-15-pro", "iphone-15-pro-max",
    "iphone-16", "iphone-16-plus", "iphone-16-pro", "iphone-16-pro-max",
    "iphone-16e",
    "iphone-17", "iphone-17-pro", "iphone-17-pro-max",
    "iphone-air",
    "iphone-se-2020-2",                               # iPhone SE 2020 (iphone-se-2020 = köpsida)
    "iphone-se-2022",
    "iphone-x", "iphone-xr",
    "iphone-xs-2",                                    # iPhone XS (iphone-xs = köpsida)
    "iphone-xs-max",
]


# ─── Hjälpfunktioner (identisk logik med FixMyPhone) ─────────────────────────

def _condition_key(
    condition: str,
    no_working: bool,
    no_display: bool,
    no_back: bool,
    no_battery: bool,
) -> str:
    suffixes = []
    if no_back:
        suffixes.append("no_back")
    if no_battery:
        suffixes.append("no_battery")
    if no_display:
        suffixes.append("no_display")
    if no_working:
        suffixes.append("no_working")
    if suffixes:
        return f"{condition}:{':'.join(suffixes)}"
    return condition


def _calc_price(
    calc: Dict,
    storage_idx: int,
    condition: str,
    no_working: bool,
    no_display: bool,
    no_back: bool,
    no_battery: bool,
) -> Optional[int]:
    variations = calc.get("variations", [])
    if storage_idx >= len(variations):
        return None

    var = variations[storage_idx]
    base_str = var.get(condition)
    if not base_str:
        return None

    price = int(base_str)

    if no_working:
        price -= int(calc.get("ifWorking", 0) or 0)
    if no_display:
        price -= int(calc.get("ifDisplay", 0) or 0)
    if no_back:
        price -= int(calc.get("ifCrackedBack", 0) or 0)
    if no_battery:
        price -= int(calc.get("ifBattery", 0) or 0)

    lowest = int(calc.get("lowest", 0) or 0)
    price = max(price, lowest)

    return price


def _storage_label_to_gb(label: str) -> Optional[int]:
    m = re.match(r"^(\d+)\s*(GB|TB)$", label.strip(), re.I)
    if not m:
        return None
    val, unit = int(m.group(1)), m.group(2).upper()
    return val * 1024 if unit == "TB" else val


def _extract_model_name(soup: BeautifulSoup, slug: str) -> str:
    """
    Läs modellnamnet från H1. Rensa bort 'Begagnad'-suffix om det dyker upp.
    Fallback: konvertera slug.
    """
    h1 = soup.find("h1", class_=re.compile(r"product.?title|entry-title", re.I))
    if not h1:
        h1 = soup.find("h1")
    if h1:
        text = h1.get_text(strip=True)
        # Rensa bort "Begagnad", priser eller andra brus-ord
        text = re.sub(r"\s+begagnad.*$", "", text, flags=re.I).strip()
        text = re.sub(r"\d[\d\s]*kr.*$", "", text, flags=re.I).strip()
        if text and len(text) < 60:
            return text

    # Fallback: slug → namn (rensa -2, -pre-loved etc.)
    clean = re.sub(r"^iphone-", "", slug, flags=re.I)
    clean = re.sub(r"-?\d+$", "", clean)  # ta bort avslutande -2, -3 etc.
    words = clean.split("-")
    result = []
    i = 0
    while i < len(words):
        w = words[i]
        if w.lower() == "se":
            result.append("SE")
        elif re.match(r"^\d+$", w):
            result.append(w)
        elif w.lower() in ("pro", "plus", "max", "mini"):
            result.append(w.capitalize())
        elif re.match(r"^\d+(st|nd|rd|th)$", w, re.I) and i + 1 < len(words) and words[i + 1].lower() == "gen":
            result.append(f"({w} generation)")
            i += 1
        else:
            result.append(w.capitalize())
        i += 1
    return "iPhone " + " ".join(result)


def _parse_model_page(html: str, slug: str) -> Optional[Dict]:
    """
    Parsa data-calc JSON. Returnerar None om sidan saknar .calcContainer
    (t.ex. köpsidor för begagnade iPhones).
    """
    soup = BeautifulSoup(html, "lxml")
    container = soup.find(class_="calcContainer")
    if not container:
        return None

    raw_json = container.get("data-calc", "")
    if not raw_json:
        return None

    try:
        calc = json.loads(raw_json)
    except json.JSONDecodeError as e:
        logger.debug(f"HappyPhone: JSON-fel för {slug}: {e}")
        return None

    if container.get("data-is-laptop", "false").lower() == "true":
        return None

    model_name = _extract_model_name(soup, slug)
    return {"model_name": model_name, "calc": calc}


def _compute_all_prices(model_name: str, calc: Dict, slug: str) -> List[Dict]:
    """
    Beräkna alla 65 prisvarianter per lagring (64 normala + water_damaged).
    """
    variations  = calc.get("variations", [])
    water_price = int(calc.get("isWaterDamaged", 60) or 60)
    model_url   = f"{PRODUCT_URL}{slug}"
    records: List[Dict] = []

    for idx, var in enumerate(variations):
        storage_gb = _storage_label_to_gb(var.get("storage", ""))
        if storage_gb is None:
            continue

        if water_price >= MIN_PRICE:
            records.append({
                "model":      model_name,
                "storage_gb": storage_gb,
                "condition":  "water_damaged",
                "price_sek":  water_price,
                "url":        model_url,
            })

        for condition in CONDITIONS:
            if not var.get(condition):
                continue

            for no_working, no_display, no_back, no_battery in iterproduct(
                (False, True), (False, True), (False, True), (False, True),
            ):
                price = _calc_price(
                    calc, idx, condition,
                    no_working, no_display, no_back, no_battery,
                )
                if price is None or price < MIN_PRICE:
                    continue

                ckey = _condition_key(condition, no_working, no_display, no_back, no_battery)
                records.append({
                    "model":      model_name,
                    "storage_gb": storage_gb,
                    "condition":  ckey,
                    "price_sek":  price,
                    "url":        model_url,
                })

    return records


# ─── Scraper-klass ────────────────────────────────────────────────────────────

class HappyPhoneScraper(BaseScraper):
    retailer_id   = "happyphone"
    retailer_name = "HappyPhone"

    async def fetch_prices(self) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(
            timeout=settings.request_timeout_seconds,
            follow_redirects=True,
            headers=HEADERS,
        ) as client:
            slugs = await self._get_iphone_slugs(client)
            if not slugs:
                logger.warning("HappyPhone: inga iPhone-slugar hittade i sitatemap")
                return []

            logger.info(f"HappyPhone: {len(slugs)} kandidater — hämtar och filtrerar parallellt")

            # Låg concurrency — Cloudflare throttlar HappyPhone vid för många parallella requests
            sem = asyncio.Semaphore(3)

            async def fetch_model(slug: str) -> Optional[Tuple[str, Dict]]:
                async with sem:
                    return await self._fetch_model(client, slug)

            model_results = await asyncio.gather(
                *[fetch_model(slug) for slug in slugs],
                return_exceptions=True,
            )

            prices: List[Dict] = []
            found_models = 0
            seen_names: set = set()

            for slug, result in zip(slugs, model_results):
                if isinstance(result, Exception) or result is None:
                    continue
                model_name, calc_data = result

                # Deduplicera: om samma modellnamn redan setts, hoppa över
                if model_name in seen_names:
                    logger.debug(f"HappyPhone: hoppar över duplikat {slug} ({model_name})")
                    continue
                seen_names.add(model_name)

                records = _compute_all_prices(model_name, calc_data, slug)
                if records:
                    found_models += 1
                prices.extend(records)

            logger.info(
                f"HappyPhone: {len(prices)} priser "
                f"({found_models} modeller, "
                f"~{len(prices) // max(found_models, 1)} kombiner/modell)"
            )
            return prices

    async def _get_iphone_slugs(self, client: httpx.AsyncClient) -> List[str]:
        """
        Hämta iPhone-slugar från WooCommerce-sitatemap.

        Köpsidor (slugar med -begagnad/-pre-loved/-fornyad-begagnad-suffix)
        filtreras bort direkt — de saknar alltid data-calc. Detta halverar
        antalet onödiga HTTP-anrop. Återstående slugar filtreras sedan i
        _fetch_model via data-calc-kontrollen.

        Sitatemap returnerar tidvis 403 (Cloudflare) — tre försök med
        backoff innan vi faller tillbaka på en känd slug-lista.
        """
        # Suffix som alltid indikerar köpsida (aldrig data-calc)
        BUY_SUFFIXES = ("-begagnad", "-pre-loved", "-fornyad-begagnad")

        for attempt in range(3):
            try:
                resp = await client.get(SITEMAP_URL)
                if resp.status_code == 403:
                    wait = 2 ** attempt
                    logger.warning(f"HappyPhone: sitatemap 403 (försök {attempt + 1}/3) — väntar {wait}s")
                    await asyncio.sleep(wait)
                    continue
                resp.raise_for_status()
                all_slugs = set(
                    re.findall(r"happyphone\.se/product/(iphone[^/<\s]+)", resp.text, re.I)
                )
                sell_slugs = sorted(
                    s for s in all_slugs
                    if not any(s.lower().endswith(sfx) for sfx in BUY_SUFFIXES)
                )
                logger.info(f"HappyPhone: {len(sell_slugs)} säljslugar ({len(all_slugs)} totalt i sitatemap)")
                return sell_slugs
            except Exception as e:
                logger.warning(f"HappyPhone: sitatemap-fel (försök {attempt + 1}/3): {e}")
                await asyncio.sleep(2 ** attempt)

        # Fallback: känd slug-lista från senaste lyckade körning
        logger.warning("HappyPhone: sitatemap otillgänglig — använder fallback-lista")
        return FALLBACK_SLUGS

    async def _fetch_model(
        self, client: httpx.AsyncClient, slug: str
    ) -> Optional[Tuple[str, Dict]]:
        """
        Hämta en produktsida och returnera (modellnamn, calc-dict) om det är en säljsida.
        Försöker upp till 3 gånger med backoff — Cloudflare kan returnera challenge-sidor
        vid hög last som ser ut som 200 men saknar data-calc.
        """
        for attempt in range(3):
            try:
                if attempt > 0:
                    await asyncio.sleep(2 ** attempt)
                resp = await client.get(f"{PRODUCT_URL}{slug}/")
                if resp.status_code != 200:
                    return None
                data = _parse_model_page(resp.text, slug)
                if data is not None:
                    return data["model_name"], data["calc"]
                # 200 men ingen data-calc — kan vara Cloudflare challenge, försök igen
                if attempt < 2:
                    logger.debug(f"HappyPhone: ingen data-calc för {slug} (försök {attempt + 1}/3)")
                    continue
                return None
            except Exception as e:
                logger.debug(f"HappyPhone: fel för {slug} (försök {attempt + 1}/3): {e}")
        return None
