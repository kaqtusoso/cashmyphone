"""
FixMyPhone-scraper – klientsidig prisberäkning via data-calc JSON.

FixMyPhone är en WooCommerce-butik där ALLA priser är inbäddade i ett
JSON-attribut (data-calc) direkt i HTML-koden för varje modellsida.
Inga API-anrop behövs efter att sidan hämtats – alla prisvarianter
beräknas lokalt med hjälp av formeln nedan.

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
{
  "variations": [
    {"storage": "256GB", "like_new": "7478", "very_good": "6660",
     "good": "5950", "acceptable": "4530"},
    ...
  ],
  "ifDisplay":      "3485",   // avdrag om skärm trasig
  "ifWorking":      "2200",   // avdrag om ej fungerar
  "ifBattery":      "1260",   // avdrag om batteri < 85%
  "ifCrackedBack":  "1758",   // avdrag om baksida trasig
  "lowest":         "770",    // garanterat minimibud (ej water_damaged)
  "isWaterDamaged": "60",     // fast pris om böjd/vatten/Face ID – åsidosätter allt
  "ifNotSWKeyboard": null     // laptop-specifikt, alltid null för iPhones
}

─── Prisformel (återskapad från klientsidig JS) ──────────────────────────────
  1. Om böjd/vatten/Face ID (water_damaged): pris = isWaterDamaged (60 kr)
  2. Annars:
       pris = variations[storage_index][condition]
       om ej fungerar:       pris -= ifWorking
       om skärm trasig:      pris -= ifDisplay
       om baksida trasig:    pris -= ifCrackedBack
       om batteri < 85%:     pris -= ifBattery
       pris = max(pris, int(lowest))
  Om ett valt avdrag saknas eller inte är numeriskt visar webbformuläret NaN.
  Den kombinationen ska då inte lagras som ett giltigt bud.
  (HappyPhone-box +200 kr hanteras inte – det är en butiksbonus, inte ett skick)

─── Condition-nyckel (lagras i condition-kolumnen) ───────────────────────────
Format: {skick}  eller  {skick}:no_back:no_battery:no_display:no_working
Suffixar i alfabetisk ordning, separerade med kolon.

  Basvillkor:   like_new | very_good | good | acceptable
  :no_back      = baksida/kameralins trasig
  :no_battery   = batteri under 85% (isBattery == 1 eller 0)
  :no_display   = skärm trasig
  :no_working   = enheten fungerar ej

  Specialfall:  water_damaged  → alltid 60 kr, ett pris per modell–lagring

─── URL-struktur ─────────────────────────────────────────────────────────────
  Listningssida:  https://salja.fixmyphone.se/salja/
  Modellsida:     https://salja.fixmyphone.se/salja/iphone-{slug}/
"""
import asyncio
import json
import logging
import re
from time import monotonic
from itertools import product as iterproduct
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from .base import BaseScraper
from ..config import settings

logger = logging.getLogger(__name__)

BASE_URL  = "https://salja.fixmyphone.se"
LIST_URL  = BASE_URL + "/"           # Startsidan listar alla modeller
SELL_URL  = BASE_URL + "/salja/"     # Prefix för enskilda modellsidor

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "sv-SE,sv;q=0.9",
}

# Visuella skicknivåer i data-calc JSON (fallande ordning)
CONDITIONS = ["like_new", "very_good", "good", "acceptable"]

# Minsta pris vi sparar (water_damaged ger 60 kr – fortfarande ett giltigt bud)
MIN_PRICE = 1
LIVE_QUOTE_CACHE_SECONDS = 60
_live_quote_cache: Dict[Tuple[str, int, str], Tuple[float, Dict[str, Any]]] = {}


# ─── Hjälpfunktioner ──────────────────────────────────────────────────────────

def _condition_key(
    condition: str,
    no_working: bool,
    no_display: bool,
    no_back: bool,
    no_battery: bool,
) -> str:
    """
    Bygg condition-nyckel med alfabetiskt sorterade suffix.

    Exempel:
      ("good", False, True, False, True)  →  "good:no_battery:no_display"
      ("like_new", False, False, False, False)  →  "like_new"
    """
    suffixes = []
    if no_back:
        suffixes.append("no_back")
    if no_battery:
        suffixes.append("no_battery")
    if no_display:
        suffixes.append("no_display")
    if no_working:
        suffixes.append("no_working")
    # no_back, no_battery, no_display, no_working är redan i alfabetisk ordning
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
    """
    Tillämpa FixMyPhones prisformel och returnera beräknat pris i SEK.
    Returnerar None om lagring/skick saknas i data-calc.
    """
    variations = calc.get("variations", [])
    if storage_idx >= len(variations):
        return None

    var = variations[storage_idx]
    base_str = var.get(condition)
    if not base_str:
        return None

    try:
        price = int(base_str)
    except (TypeError, ValueError):
        return None

    deductions = (
        ("ifWorking", no_working),
        ("ifDisplay", no_display),
        ("ifCrackedBack", no_back),
        ("ifBattery", no_battery),
    )
    for field, enabled in deductions:
        if not enabled:
            continue
        raw_value = calc.get(field)
        if raw_value is None or raw_value == "":
            return None
        try:
            price -= int(raw_value)
        except (TypeError, ValueError):
            return None

    # Garanterat minimibud från FixMyPhone
    lowest = int(calc.get("lowest", 0) or 0)
    price = max(price, lowest)

    return price


def _storage_label_to_gb(label: str) -> Optional[int]:
    """'256GB' → 256, '1TB' → 1024."""
    m = re.match(r"^(\d+)\s*(GB|TB)$", label.strip(), re.I)
    if not m:
        return None
    val, unit = int(m.group(1)), m.group(2).upper()
    return val * 1024 if unit == "TB" else val


def _slug_to_model_name(soup: BeautifulSoup, slug: str) -> str:
    """
    Läs modellnamnet från sidans H1. Fallback: konvertera slug.
    iphone-17-pro-max → iPhone 17 Pro Max
    """
    # Försök WooCommerce product title (H1)
    h1 = soup.find("h1", class_=re.compile(r"product.?title|entry-title", re.I))
    if not h1:
        h1 = soup.find("h1")
    if h1:
        text = h1.get_text(strip=True)
        # Rensa bort eventuellt pris som hamnat i H1
        text = re.sub(r"\d[\d\s]*kr.*$", "", text, flags=re.I).strip()
        if text and len(text) < 60:
            return text

    # Fallback: konvertera slug direkt
    without_prefix = re.sub(r"^iphone-", "", slug, flags=re.I)
    words = without_prefix.split("-")
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
            i += 1  # hoppa över "gen"
        else:
            result.append(w.capitalize())
        i += 1

    return "iPhone " + " ".join(result)


def _parse_model_page(html: str, slug: str) -> Optional[Dict]:
    """
    Parsa data-calc JSON och extrahera modellnamn + prisdata.

    Returnerar:
      {"model_name": "iPhone 17 Pro", "calc": {...}}
    eller None om sidan inte innehåller .calcContainer med data-calc.
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
        logger.debug(f"FixMyPhone: JSON-fel för {slug}: {e}")
        return None

    # Hoppa över laptops (data-is-laptop='true')
    if container.get("data-is-laptop", "false").lower() == "true":
        return None

    model_name = _slug_to_model_name(soup, slug)

    return {"model_name": model_name, "calc": calc}


def _compute_all_prices(
    model_name: str,
    calc: Dict,
    slug: str,
) -> List[Dict]:
    """
    Beräkna alla prisvarianter för en modell från data-calc.

    Per lagring genereras:
      64 kombinationer  (4 skick × 2^4 felflaggor)
      + 1 water_damaged  (fast 60 kr)
    """
    variations  = calc.get("variations", [])
    water_price = int(calc.get("isWaterDamaged", 60) or 60)
    model_url   = f"{SELL_URL}{slug}"
    records: List[Dict] = []

    missing_deductions = [
        field
        for field in ("ifWorking", "ifDisplay", "ifCrackedBack", "ifBattery")
        if calc.get(field) is None or calc.get(field) == ""
    ]
    if missing_deductions:
        logger.warning(
            "FixMyPhone: %s (%s) saknar avdrag %s; berörda felkombinationer utelämnas",
            model_name,
            slug,
            ", ".join(missing_deductions),
        )

    for idx, var in enumerate(variations):
        storage_label = var.get("storage", "")
        storage_gb    = _storage_label_to_gb(storage_label)
        if storage_gb is None:
            logger.debug(f"FixMyPhone: okänd lagring '{storage_label}' för {slug}")
            continue

        # water_damaged: fast pris, åsidosätter alla skick och fel
        if water_price >= MIN_PRICE:
            records.append({
                "model":      model_name,
                "storage_gb": storage_gb,
                "condition":  "water_damaged",
                "price_sek":  water_price,
                "url":        model_url,
            })

        # Alla 64 normala kombinationer per lagring
        for condition in CONDITIONS:
            if not var.get(condition):
                continue  # detta skick finns ej för lagringen

            for no_working, no_display, no_back, no_battery in iterproduct(
                (False, True),
                (False, True),
                (False, True),
                (False, True),
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

class FixMyPhoneScraper(BaseScraper):
    retailer_id   = "fixmyphone"
    retailer_name = "FixMyPhone"
    min_models = 20
    min_rows = 1000
    expected_conditions = frozenset(
        {
            _condition_key(condition, no_working, no_display, no_back, no_battery)
            for condition in CONDITIONS
            for no_working, no_display, no_back, no_battery in iterproduct(
                (False, True), repeat=4
            )
        }
        | {"water_damaged"}
    )

    async def fetch_live_quote(
        self,
        model_url: str,
        storage_gb: int,
        condition: str,
    ) -> Optional[Dict[str, Any]]:
        """Beräkna vald rad från FixMyPhones aktuella officiella data-calc."""
        parsed_url = urlparse(model_url)
        if parsed_url.scheme != "https" or parsed_url.hostname not in {
            "salja.fixmyphone.se", "www.salja.fixmyphone.se",
        }:
            return None
        parts = [part for part in parsed_url.path.split("/") if part]
        if len(parts) != 2 or parts[0] != "salja":
            return None
        slug = parts[1]
        normalized_condition = condition.lower()
        cache_key = (slug, storage_gb, normalized_condition)
        cached = _live_quote_cache.get(cache_key)
        if cached and monotonic() - cached[0] < LIVE_QUOTE_CACHE_SECONDS:
            return dict(cached[1])

        async with httpx.AsyncClient(
            timeout=settings.request_timeout_seconds,
            follow_redirects=True,
            headers=HEADERS,
        ) as client:
            response = await client.get(f"{SELL_URL}{slug}/")
            response.raise_for_status()

        model = _parse_model_page(response.text, slug)
        if not model:
            return None
        rows = _compute_all_prices(model["model_name"], model["calc"], slug)
        quote = next(
            (
                row for row in rows
                if row["storage_gb"] == storage_gb
                and row["condition"].lower() == normalized_condition
            ),
            None,
        )
        if quote:
            _live_quote_cache[cache_key] = (monotonic(), dict(quote))
        return quote

    async def fetch_prices(self) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(
            timeout=settings.request_timeout_seconds,
            follow_redirects=True,
            headers=HEADERS,
        ) as client:
            # Steg 1: Hämta iPhone-slugar från listningssidan
            slugs = await self._get_iphone_slugs(client)
            if not slugs:
                logger.warning("FixMyPhone: inga iPhone-slugar hittade")
                return []

            logger.info(f"FixMyPhone: {len(slugs)} modeller hittade — hämtar parallellt")

            # Steg 2: Hämta och parsa alla modellsidor parallellt
            sem = asyncio.Semaphore(8)

            async def fetch_model(slug: str) -> Optional[Tuple[str, Dict]]:
                async with sem:
                    return await self._fetch_model(client, slug)

            model_results = await asyncio.gather(
                *[fetch_model(slug) for slug in slugs],
                return_exceptions=True,
            )

            # Steg 3: Beräkna priser lokalt — inga extra HTTP-anrop
            prices: List[Dict] = []
            found_models = 0

            for slug, result in zip(slugs, model_results):
                if isinstance(result, Exception) or result is None:
                    continue
                model_name, calc_data = result
                records = _compute_all_prices(model_name, calc_data, slug)
                if records:
                    found_models += 1
                prices.extend(records)

            logger.info(
                f"FixMyPhone: {len(prices)} priser "
                f"({found_models} modeller, "
                f"~{len(prices) // max(found_models, 1)} kombiner/modell)"
            )
            return prices

    async def _get_iphone_slugs(self, client: httpx.AsyncClient) -> List[str]:
        """Hitta alla iPhone-produktslugar från FixMyPhones startsida."""
        try:
            resp = await client.get(LIST_URL)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")
            slugs: set = set()
            for a in soup.find_all("a", href=True):
                m = re.match(
                    r"^(?:https?://salja\.fixmyphone\.se)?/salja/(iphone[^/]+)/?$",
                    a["href"], re.I,
                )
                if m:
                    slugs.add(m.group(1).lower())
            return sorted(slugs)
        except Exception as e:
            logger.error(f"FixMyPhone: fel vid slug-hämtning: {e}")
            return []

    async def _fetch_model(
        self, client: httpx.AsyncClient, slug: str
    ) -> Optional[Tuple[str, Dict]]:
        """Hämta en modellsida och returnera (modellnamn, calc-dict)."""
        try:
            resp = await client.get(f"{SELL_URL}{slug}")
            if resp.status_code != 200:
                logger.debug(f"FixMyPhone: {slug} → HTTP {resp.status_code}")
                return None
            data = _parse_model_page(resp.text, slug)
            if data is None:
                return None
            return data["model_name"], data["calc"]
        except Exception as e:
            logger.debug(f"FixMyPhone: fel för {slug}: {e}")
            return None
