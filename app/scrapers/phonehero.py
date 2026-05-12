"""
PhoneHero-scraper – parallell modell-hämtning.

Livewire-baserad scraper som hämtar alla modeller via ?model={slug}.
Optimering: kör upp till 8 HTTP-förfrågningar parallellt med asyncio.Semaphore.
"""
import httpx
import logging
import json
import re
import asyncio
from typing import List, Dict, Any, Optional
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


class PhoneHeroScraper(BaseScraper):
    retailer_id = "phonehero"
    retailer_name = "PhoneHero"

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

            payload = {
                "components": [{
                    "snapshot": mod_snap_raw,
                    "updates": {"searchterm": "iPhone"},
                    "calls": [],
                }]
            }
            headers = {
                **HEADERS,
                "X-CSRF-TOKEN": csrf,
                "X-Livewire": "true",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Referer": SELL_URL,
            }
            r2 = await client.post(livewire_url, json=payload, headers=headers)
            if r2.status_code != 200:
                return []

            data = r2.json()
            comp = data.get("components", [{}])[0]
            new_snap = json.loads(comp.get("snapshot", "{}"))
            results = new_snap.get("data", {}).get("results", [])

            items = results[0] if results and isinstance(results[0], list) else results
            slugs = []
            for entry in items:
                item_data = entry[0].get("item", []) if isinstance(entry, list) else []
                if item_data:
                    model = item_data[0]
                    slug = model.get("slug", "")
                    name = model.get("name", "")
                    if slug and "iphone" in slug.lower():
                        clean_name = re.sub(r"^Apple\s+", "", name).strip()
                        slugs.append((slug, clean_name))

            return slugs

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
            working_model = snap.get("data", {}).get("workingModel")
            if not working_model:
                return []

            wm = working_model[0] if isinstance(working_model, list) else working_model
            sizes = wm.get("sizes", [])
            if not sizes:
                return []

            sizes_list = sizes[0] if isinstance(sizes[0], list) else sizes

            prices = []
            for size_entry in sizes_list:
                if not isinstance(size_entry, list) or not size_entry:
                    continue
                size = size_entry[0]
                storage_str = size.get("name", "")
                base_price = size.get("price", 0)
                if not base_price or base_price <= 0:
                    continue
                prices.append({
                    "model": model_name,
                    "storage_gb": self._parse_storage(storage_str),
                    "condition": "nyskick",
                    "price_sek": int(base_price),
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
