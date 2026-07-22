"""
PhoneHero-scraper – fullständiga skickskombinationer från Livewire-snapshot.

PhoneHero bäddar in hela säljkalkylen i Livewire-state för varje modell:

  selected storage price = baspris
  buyquestions[].answers[] = avdrag per svar
    modifytype="kronor"  -> dra av fast belopp
    modifytype="procent" -> dra av procent av baspriset

Vi behöver alltså inte klicka igenom varje kombination server-side. För varje
modell genereras alla kombinationer av lagring × ett svar per fråga.

Condition-nyckel:
  s=n|b=ms|d=no|c=no|bt=ok
  dev=n|d=no|c=no

Vissa nyare modeller har en enda "device"-skickfråga i stället för separata
screen/body-frågor. Äldre modeller har ofta screen + body + battery.
"""
import httpx
import logging
import json
import re
import asyncio
import unicodedata
from itertools import product
from typing import List, Dict, Any, Optional, Iterable, Mapping
from bs4 import BeautifulSoup
from .base import BaseScraper
from ..config import settings

logger = logging.getLogger(__name__)

SELL_URL = "https://phonehero.se/salj-din-gamla-mobil-till-oss"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "sv-SE,sv;q=0.9",
}

STORAGE_RE = re.compile(r"(\d+)\s*(GB|TB)", re.I)


def _unwrap_livewire(value):
    """Ta bort Livewires metadata-wrapper [value, {"s": "..."}]."""
    if (
        isinstance(value, list)
        and len(value) == 2
        and isinstance(value[1], dict)
        and "s" in value[1]
    ):
        return _unwrap_livewire(value[0])
    if isinstance(value, list):
        return [_unwrap_livewire(v) for v in value]
    if isinstance(value, dict):
        return {k: _unwrap_livewire(v) for k, v in value.items()}
    return value


def _slugify_label(label: str) -> str:
    normalized = unicodedata.normalize("NFKD", label or "")
    ascii_label = normalized.encode("ascii", "ignore").decode("ascii")
    key = re.sub(r"[^a-z0-9]+", "_", ascii_label.lower()).strip("_")
    return key[:40] or "unknown"


def _answer_key(label: str) -> str:
    """Kompakt, stabil nyckel för svenska PhoneHero-svar."""
    text = (label or "").lower()
    if "nyskick" in text:
        return "n"
    if "normalt sliten" in text:
        return "ns"
    if "mycket sliten" in text:
        return "ms"
    if "sprickor i glaset" in text:
        return "sg"
    if "trasig lcd" in text:
        return "lcd"
    if "sprucket glas" in text and "fram och baksida" in text:
        return "sfb"
    if "sprucket glas" in text and "framsida" in text:
        return "sf"
    if "sprucket glas" in text and "baksida" in text:
        return "sb"
    if text.strip() == "sprickor":
        return "sp"
    if text.strip() == "nej":
        return "no"
    if "face-id" in text or "face id" in text:
        return "fid"
    if "fingeravtryck" in text or "touch id" in text or "touch-id" in text:
        return "fp"
    if "ljudet" in text:
        return "snd"
    if "startar inte" in text:
        return "off"
    if "kamera" in text:
        return "cam"
    if "annat fel" in text:
        return "oth"
    if "ja, men" in text and "fungerar" in text:
        return "yok"
    if "ja, och" in text:
        return "ybad"
    if "minst 85" in text:
        return "ok"
    if "lägre än 85" in text or "lagre an 85" in _slugify_label(text):
        return "low"
    return _slugify_label(label)


def _question_key(question: Dict[str, Any], condition_index: int) -> str:
    qtype = question.get("questionType", "")
    label = (question.get("question", {}) or {}).get("sv", "").lower()

    if qtype == "condition":
        if "skärmen" in label:
            return "s"
        if "sidorna" in label or "baksidan" in label:
            return "b"
        return "dev" if condition_index == 0 else f"cond{condition_index + 1}"
    if qtype == "defects":
        return "d"
    if qtype == "criticaldamage":
        return "c"
    if qtype == "batteryhealth":
        return "bt"
    return f"q{question.get('sortid', 'x')}"


def _condition_key(selections: List[Dict[str, Any]]) -> str:
    return "|".join(f"{s['question_key']}={s['answer_key']}" for s in selections)


def _calc_price(base_price: int, selections: List[Dict[str, Any]]) -> int:
    kronor = 0
    percent = 0.0
    for selection in selections:
        try:
            modify = float(selection.get("modify") or 0)
        except (TypeError, ValueError):
            modify = 0
        if selection.get("modifytype") == "procent":
            percent += modify
        else:
            kronor += round(modify)

    price = round(base_price - (base_price * percent / 100) - kronor)
    return _round_display_price(price)


def _round_display_price(price: int) -> int:
    """PhoneHero visar bud takavrundade till närmaste tiotal."""
    if price <= 0:
        return 0
    return ((price + 9) // 10) * 10


class PhoneHeroScraper(BaseScraper):
    retailer_id = "phonehero"
    retailer_name = "PhoneHero"
    min_models = 20
    min_rows = 5000
    expected_condition_count = 20

    _allowed_answers = {
        "s": {"n", "ns", "ms", "sg", "lcd"},
        "b": {"n", "ns", "ms", "sp"},
        "dev": {"n", "ns", "ms", "sf", "sb", "sfb"},
        "d": {"no", "fid", "fp", "snd", "off", "cam", "oth"},
        "c": {"no", "yok", "ybad"},
        "bt": {"ok", "low"},
    }

    async def validate_prices(
        self,
        prices: Iterable[Mapping[str, Any]],
        db,
    ) -> List[Dict[str, Any]]:
        rows = await super().validate_prices(prices, db)
        for row in rows:
            condition = str(row["condition"])
            for part in condition.split("|"):
                if "=" not in part:
                    raise RuntimeError(f"PhoneHero: ogiltig condition-nyckel {condition}")
                question, answer = part.split("=", 1)
                if question not in self._allowed_answers or answer not in self._allowed_answers[question]:
                    raise RuntimeError(
                        f"PhoneHero: okänt formulärsvar {question}={answer}; import stoppad"
                    )
        return rows

    async def fetch_prices(self) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(
            timeout=settings.request_timeout_seconds,
            follow_redirects=True,
            headers=HEADERS,
        ) as client:
            slugs = await self._get_iphone_slugs(client)
            if not slugs:
                logger.warning("PhoneHero: inga modell-slugar hittade")
                return []

            logger.info(f"PhoneHero: {len(slugs)} modeller – hämtar parallellt (8 åt gången)")

            sem = asyncio.Semaphore(8)

            async def fetch_with_sem(slug: str, name: str) -> List[Dict]:
                async with sem:
                    return await self._fetch_model_prices(client, slug, name)

            results = await asyncio.gather(
                *[fetch_with_sem(slug, name) for slug, name in slugs],
                return_exceptions=True,
            )

            prices = []
            for result in results:
                if isinstance(result, list):
                    prices.extend(result)

            return prices

    async def _get_iphone_slugs(self, client: httpx.AsyncClient) -> List[tuple]:
        try:
            resp = await client.get(SELL_URL)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            csrf = self._get_csrf(soup)
            livewire_url = self._get_livewire_url(resp.text)
            mod_snap_raw = self._get_snapshot_raw(soup, "modellsok")

            if not all([csrf, livewire_url, mod_snap_raw]):
                return []

            headers = {
                **HEADERS,
                "X-CSRF-TOKEN": csrf,
                "X-Livewire": "true",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Referer": SELL_URL,
            }

            # "iPhone" returnerar bara de populäraste resultaten. Lägg till
            # specifika sökningar så nya modeller som iPhone 17/Air också fångas.
            search_terms = ["iPhone", "iPhone 17", "iPhone Air"]
            slugs: Dict[str, str] = {}

            for term in search_terms:
                payload = {
                    "components": [{
                        "snapshot": mod_snap_raw,
                        "updates": {"searchterm": term},
                        "calls": [],
                    }]
                }
                r2 = await client.post(livewire_url, json=payload, headers=headers)
                if r2.status_code != 200:
                    continue

                data = r2.json()
                comp = data.get("components", [{}])[0]
                new_snap = json.loads(comp.get("snapshot", "{}"))
                results = _unwrap_livewire(new_snap.get("data", {}).get("results", []))

                for entry in results:
                    item = entry.get("item") if isinstance(entry, dict) else None
                    if not item:
                        continue
                    model = item[0] if isinstance(item, list) else item
                    slug = model.get("slug", "")
                    name = model.get("name", "")
                    if slug and slug.lower().startswith("iphone"):
                        slugs[slug] = re.sub(r"^Apple\s+", "", name).strip()

            return sorted(slugs.items(), key=lambda item: item[1])

        except Exception as e:
            logger.exception(f"PhoneHero: fel vid slug-hämtning: {e}")
            return []

    async def _fetch_model_prices(
        self, client: httpx.AsyncClient, slug: str, model_name: str
    ) -> List[Dict]:
        try:
            resp = await client.get(SELL_URL, params={"model": slug})
            if resp.status_code != 200:
                return []

            soup = BeautifulSoup(resp.text, "lxml")
            snap_raw = self._get_snapshot_raw(soup, "selldevice")
            if not snap_raw:
                return []

            snap = json.loads(snap_raw)
            working_model = _unwrap_livewire(snap.get("data", {}).get("workingModel"))
            if not working_model:
                return []

            wm = working_model[0] if isinstance(working_model, list) else working_model
            sizes = wm.get("sizes", [])
            if not sizes:
                return []

            sizes_list = sizes
            questions = self._parse_questions(wm.get("buyquestions", []))

            prices = []
            for size in sizes_list:
                if not isinstance(size, dict):
                    continue
                storage_str = size.get("name", "")
                base_price = size.get("price", 0)
                if not base_price or base_price <= 0:
                    continue

                if not questions:
                    prices.append({
                        "model": model_name,
                        "storage_gb": self._parse_storage(storage_str),
                        "condition": "nyskick",
                        "price_sek": _round_display_price(int(base_price)),
                        "url": f"{SELL_URL}?model={slug}",
                    })
                    continue

                for selections in product(*questions):
                    selected = list(selections)
                    prices.append({
                        "model": model_name,
                        "storage_gb": self._parse_storage(storage_str),
                        "condition": _condition_key(selected),
                        "price_sek": _calc_price(int(base_price), selected),
                        "url": f"{SELL_URL}?model={slug}",
                    })

            return prices

        except Exception as e:
            logger.debug(f"PhoneHero: fel för {slug}: {e}")
            return []

    def _get_csrf(self, soup: BeautifulSoup) -> Optional[str]:
        meta = soup.find("meta", {"name": "csrf-token"})
        return meta["content"] if meta else None

    def _get_livewire_url(self, html: str) -> Optional[str]:
        m = re.search(r'data-update-uri="([^"]+)"', html)
        if m:
            uri = m.group(1)
            return uri if uri.startswith("http") else f"https://phonehero.se{uri}"
        m = re.search(r"(livewire[a-z0-9\-]*/update)", html)
        if m:
            return f"https://phonehero.se/{m.group(1)}"
        return "https://phonehero.se/livewire/update"

    def _get_snapshot_raw(self, soup: BeautifulSoup, component: str) -> Optional[str]:
        el = soup.find(attrs={"wire:name": component})
        return el.get("wire:snapshot") if el else None

    def _parse_storage(self, storage_str: str) -> Optional[int]:
        m = STORAGE_RE.search(storage_str)
        if not m:
            return None
        value = int(m.group(1))
        unit = m.group(2).upper()
        return value * 1024 if unit == "TB" else value

    def _parse_questions(self, raw_questions: Any) -> List[List[Dict[str, Any]]]:
        questions = _unwrap_livewire(raw_questions)
        parsed: List[List[Dict[str, Any]]] = []
        condition_index = 0

        for question in questions:
            if not isinstance(question, dict):
                continue
            qkey = _question_key(question, condition_index)
            if question.get("questionType") == "condition":
                condition_index += 1

            answers = []
            for answer in question.get("answers", []):
                if not isinstance(answer, dict):
                    continue
                sv_label = (answer.get("answer", {}) or {}).get("sv", "")
                answers.append({
                    "question_key": qkey,
                    "answer_key": _answer_key(sv_label),
                    "modify": answer.get("modify", 0),
                    "modifytype": answer.get("modifytype", "kronor"),
                })
            if answers:
                parsed.append(answers)

        return parsed
