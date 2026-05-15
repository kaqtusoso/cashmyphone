"""
Telestore-scraper — fullständiga skickskombinationer via intern pris-API.

─── Formulärstruktur ─────────────────────────────────────────────────────────
Telestore har ett 5-stegs formulär med globala, konsekventa option-ID:n
för alla iPhone-modeller:

  Kriterie 20 – "Fungerar telefonen som den ska?"
    18 = Ja   19 = Nej

  Kriterie 21 – "Är din telefon böjd eller vattenskadad?"
    21 = Nej   22 = Ja

  Kriterie 23 – "Vilket skick är telefonen i?"
    27 = Nyskick       (inga tecken på användning)
    28 = Utmärkt       (små tecken)
    29 = Bra           (flera repor/kantstötning)
    30 = Okej          (mycket repor/kantstötningar)
    53 = Sprickor fram (glassprickor eller LCD-fel)

  Kriterie 25 – "Är sidorna eller baksidan trasig?"
    34 = Nej   35 = Ja

  Kriterie 26 – "Är din batterihälsa 85% eller högre?"
    48 = Ja   49 = Nej

─── Pris-API ─────────────────────────────────────────────────────────────────
POST https://telestore.se/salja-mobil/{slug}/?action=ajax-get-price
FormData: storageID, unitID, options (JSON-array med {criteriaID, id, isSlider})
Svar: {"price": 6410.0}

─── Condition-nyckel (lagras i condition-kolumnen) ───────────────────────────
Format: {skick}  eller  {skick}:bat  eller  {skick}:sidor  eller  {skick}:bat:sidor

  nyskick, utmarkt, bra, okej, sprickor_fram
  :bat      = batterihälsa under 85%
  :sidor    = sidor eller baksida trasig

Vi lagrar INTE kombinationer där telefonen inte fungerar (19).
Böjd/vattenskadad (22) lagras som "water_damaged" — Telestore erbjuder 60 kr
och det är ett accepterat bud hos CashMyPhone.
"""
import asyncio
import logging
import re
import json
from itertools import product
from typing import Any, Dict, List, Optional, Tuple

import httpx
from bs4 import BeautifulSoup

from .base import BaseScraper
from ..config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://telestore.se"
SELL_URL = f"{BASE_URL}/salja-mobil/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "sv-SE,sv;q=0.9",
}

# Globala option-ID:n — identiska för alla iPhone-modeller på Telestore
CRIT_FUNGERAR    = 20  # Fungerar telefonen?
CRIT_VATTEN      = 21  # Böjd eller vattenskadad?
CRIT_SKICK       = 23  # Vilket skick?
CRIT_SIDOR       = 25  # Sidor/baksida trasig?
CRIT_BATTERI     = 26  # Batterihälsa ≥85%?

OPT_FUNGERAR_JA  = 18
OPT_VATTEN_NEJ   = 21
OPT_VATTEN_JA    = 22   # Böjd/vattenskadad → alltid 60 kr
OPT_BATTERI_OK   = 48   # Ja, ≥85%
OPT_BATTERI_LAG  = 49   # Nej, <85%
OPT_SIDOR_OK     = 34   # Nej, ej trasig
OPT_SIDOR_TRASIG = 35   # Ja, trasig

# skick-option-id → condition-nyckelprefix
SKICK_OPTIONS: List[Tuple[int, str]] = [
    (27, "nyskick"),
    (28, "utmarkt"),
    (29, "bra"),
    (30, "okej"),
    (53, "sprickor_fram"),
]

MIN_PRICE = 1  # Inkludera alla bud — även 60 kr är ett giltigt bud


def _build_options(skick_id: int, batteri_id: int, sidor_id: int) -> List[Dict]:
    return [
        {"criteriaID": CRIT_FUNGERAR, "id": OPT_FUNGERAR_JA, "isSlider": 0},
        {"criteriaID": CRIT_VATTEN,   "id": OPT_VATTEN_NEJ,  "isSlider": 0},
        {"criteriaID": CRIT_SKICK,    "id": skick_id,        "isSlider": 0},
        {"criteriaID": CRIT_SIDOR,    "id": sidor_id,        "isSlider": 0},
        {"criteriaID": CRIT_BATTERI,  "id": batteri_id,      "isSlider": 0},
    ]


def _condition_key(skick_label: str, batteri_id: int, sidor_id: int) -> str:
    key = skick_label
    if batteri_id == OPT_BATTERI_LAG:
        key += ":bat"
    if sidor_id == OPT_SIDOR_TRASIG:
        key += ":sidor"
    return key


def _storage_gb(space: int) -> int:
    """Telestore använder 1000 för 1TB — konvertera till 1024."""
    return 1024 if space >= 900 else space


def _parse_model_page(html: str) -> Optional[Dict]:
    """Extrahera unitID, unitName och storage-alternativ från en modellsida."""
    m = re.search(r'WGR\.sellUnit\.init\(\{(.*?)\}\);', html, re.DOTALL)
    if not m:
        return None
    raw = m.group(1)

    uid   = re.search(r'unitID:\s*(\d+)', raw)
    uname = re.search(r'unitName:\s*"([^"]+)"', raw)
    sm    = re.search(r'storage:\s*(\[.+?\])', raw, re.DOTALL)

    if not (uid and uname and sm):
        return None

    try:
        storages = json.loads(sm.group(1))
    except json.JSONDecodeError:
        return None

    return {
        "unit_id":   int(uid.group(1)),
        "unit_name": uname.group(1).strip(),
        "storages":  storages,  # [{id, space, price}]
    }


class TelestoreScraper(BaseScraper):
    retailer_id = "telestore"
    retailer_name = "Telestore"

    async def fetch_prices(self) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(
            timeout=settings.request_timeout_seconds,
            follow_redirects=True,
            headers=HEADERS,
        ) as client:
            # Steg 1: Hämta alla iPhone-slugar från säljsidan
            slugs = await self._get_iphone_slugs(client)
            if not slugs:
                logger.warning("Telestore: inga iPhone-slugar hittade")
                return []

            logger.info(f"Telestore: {len(slugs)} modeller hittade — hämtar parallellt")

            # Steg 2: Hämta modellsidor parallellt
            sem = asyncio.Semaphore(8)

            async def fetch_model(slug: str) -> Optional[Dict]:
                async with sem:
                    return await self._fetch_model_data(client, slug)

            model_results = await asyncio.gather(
                *[fetch_model(slug) for slug in slugs],
                return_exceptions=True,
            )

            # Steg 3: Hämta alla priskombinationer parallellt
            price_tasks = []
            for slug, result in zip(slugs, model_results):
                if isinstance(result, Exception) or result is None:
                    continue
                for storage in result["storages"]:
                    for skick_id, skick_label in SKICK_OPTIONS:
                        for batteri_id in (OPT_BATTERI_OK, OPT_BATTERI_LAG):
                            for sidor_id in (OPT_SIDOR_OK, OPT_SIDOR_TRASIG):
                                price_tasks.append((
                                    slug, result, storage,
                                    skick_id, skick_label,
                                    batteri_id, sidor_id,
                                ))

            logger.info(f"Telestore: {len(price_tasks)} priskombinationer att hämta")

            price_sem = asyncio.Semaphore(15)

            async def fetch_price_combo(task):
                async with price_sem:
                    slug, model, storage, skick_id, skick_label, batteri_id, sidor_id = task
                    return await self._fetch_price(
                        client, slug, model, storage,
                        skick_id, skick_label, batteri_id, sidor_id,
                    )

            combo_results = await asyncio.gather(
                *[fetch_price_combo(t) for t in price_tasks],
                return_exceptions=True,
            )

            prices = []
            for result in combo_results:
                if isinstance(result, Exception) or result is None:
                    continue
                prices.append(result)

            # Steg 4: Hämta water_damaged-priset (60 kr) per modell och lagring
            water_tasks = []
            for slug, result in zip(slugs, model_results):
                if isinstance(result, Exception) or result is None:
                    continue
                for storage in result["storages"]:
                    water_tasks.append((slug, result, storage))

            async def fetch_water(task):
                async with price_sem:
                    slug, model, storage = task
                    return await self._fetch_water_damaged(client, slug, model, storage)

            water_results = await asyncio.gather(
                *[fetch_water(t) for t in water_tasks],
                return_exceptions=True,
            )
            for result in water_results:
                if isinstance(result, Exception) or result is None:
                    continue
                prices.append(result)

            logger.info(f"Telestore: {len(prices)} priser sparade")
            return prices

    async def _get_iphone_slugs(self, client: httpx.AsyncClient) -> List[str]:
        try:
            resp = await client.get(SELL_URL)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")
            slugs = set()
            for a in soup.find_all("a", href=True):
                m = re.match(r"^/salja-mobil/(iphone[^/]+)/$", a["href"], re.I)
                if m:
                    slugs.add(m.group(1))
            return sorted(slugs)
        except Exception as e:
            logger.error(f"Telestore: fel vid slug-hämtning: {e}")
            return []

    async def _fetch_model_data(
        self, client: httpx.AsyncClient, slug: str
    ) -> Optional[Dict]:
        try:
            resp = await client.get(f"{SELL_URL}{slug}/")
            if resp.status_code != 200:
                return None
            data = _parse_model_page(resp.text)
            if data:
                data["slug"] = slug
            return data
        except Exception as e:
            logger.debug(f"Telestore: fel för {slug}: {e}")
            return None

    async def _fetch_price(
        self,
        client: httpx.AsyncClient,
        slug: str,
        model: Dict,
        storage: Dict,
        skick_id: int,
        skick_label: str,
        batteri_id: int,
        sidor_id: int,
    ) -> Optional[Dict]:
        try:
            options = _build_options(skick_id, batteri_id, sidor_id)
            url = f"{SELL_URL}{slug}/?action=ajax-get-price"
            resp = await client.post(url, data={
                "storageID": storage["id"],
                "unitID":    model["unit_id"],
                "options":   json.dumps(options),
            }, headers={**HEADERS, "Referer": f"{SELL_URL}{slug}/"})

            if resp.status_code != 200:
                return None

            data = resp.json()
            price = data.get("price")
            if not price or float(price) < MIN_PRICE:
                return None

            condition = _condition_key(skick_label, batteri_id, sidor_id)
            model_name = f"iPhone {model['unit_name']}"
            storage_gb = _storage_gb(storage["space"])

            return {
                "model":      model_name,
                "storage_gb": storage_gb,
                "condition":  condition,
                "price_sek":  round(float(price)),
                "url":        f"{SELL_URL}{slug}/",
            }
        except Exception as e:
            logger.debug(f"Telestore: prisfel {slug} {storage.get('space')}GB: {e}")
            return None

    async def _fetch_water_damaged(
        self,
        client: httpx.AsyncClient,
        slug: str,
        model: Dict,
        storage: Dict,
    ) -> Optional[Dict]:
        """
        Hämta priset för böjd/vattenskadad telefon (option 22).
        Telestore returnerar alltid 60 kr oavsett skick — vi skickar nyskick
        som bas men det spelar ingen roll för slutpriset.
        """
        try:
            options = [
                {"criteriaID": CRIT_FUNGERAR, "id": OPT_FUNGERAR_JA,  "isSlider": 0},
                {"criteriaID": CRIT_VATTEN,   "id": OPT_VATTEN_JA,    "isSlider": 0},
                {"criteriaID": CRIT_SKICK,    "id": 27,               "isSlider": 0},  # nyskick
                {"criteriaID": CRIT_SIDOR,    "id": OPT_SIDOR_OK,     "isSlider": 0},
                {"criteriaID": CRIT_BATTERI,  "id": OPT_BATTERI_OK,   "isSlider": 0},
            ]
            url = f"{SELL_URL}{slug}/?action=ajax-get-price"
            resp = await client.post(url, data={
                "storageID": storage["id"],
                "unitID":    model["unit_id"],
                "options":   json.dumps(options),
            }, headers={**HEADERS, "Referer": f"{SELL_URL}{slug}/"})

            if resp.status_code != 200:
                return None

            data = resp.json()
            price = data.get("price")
            if not price or float(price) < MIN_PRICE:
                return None

            return {
                "model":      f"iPhone {model['unit_name']}",
                "storage_gb": _storage_gb(storage["space"]),
                "condition":  "water_damaged",
                "price_sek":  round(float(price)),
                "url":        f"{SELL_URL}{slug}/",
            }
        except Exception as e:
            logger.debug(f"Telestore: water_damaged-fel {slug}: {e}")
            return None
