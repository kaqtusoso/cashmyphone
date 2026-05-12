"""
PhoneHero-scraper

PhoneHero's sälj-sida (https://phonehero.se/salj-din-gamla-mobil-till-oss)
använder Laravel Livewire. När du skickar ?model={slug} i URL:en bäddar
sidan in komplett prisdata i wire:snapshot för selldevice-komponenten —
inklusive alla lagringsstorlekar och skick-justeringar.

Flöde:
  1. Hämta startsidan och sök "iPhone" via Livewire → lista med modell-slugar
  2. För varje slug: GET ?model={slug} → extrahera sizes[].price (basbelopp)
  3. Skicket "nyskick" (best) = inget avdrag från basbeloppet
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
            # Steg 1: hämta alla iPhone-modell-slugar via Livewire-sökning
            slugs = await self._get_iphone_slugs(client)
            if not slugs:
                logger.warning("PhoneHero: inga modell-slugar hittade")
                return []

            logger.info(f"PhoneHero: hittade {len(slugs)} modeller att hämta priser för")

            prices: List[Dict] = []
            for slug, name in slugs:
                model_prices = await self._fetch_model_prices(client, slug, name)
                prices.extend(model_prices)
                await asyncio.sleep(0.3)  # Var snäll mot servern

            return prices

    # ─── Steg 1: hitta alla iPhone-slugar ───────────────────────────────────

    async def _get_iphone_slugs(self, client: httpx.AsyncClient) -> List[tuple]:
        """Hämta alla iPhone-modeller med slug och namn via Livewire-sökning."""
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

            # results är en nästlad lista: results[0] är listan med träffar
            items = results[0] if results and isinstance(results[0], list) else results
            slugs = []
            for entry in items:
                item_data = entry[0].get("item", []) if isinstance(entry, list) else []
                if item_data:
                    model = item_data[0]
                    slug = model.get("slug", "")
                    name = model.get("name", "")
                    if slug and "iphone" in slug.lower():
                        # Rensa "Apple " prefix
                        clean_name = re.sub(r"^Apple\s+", "", name).strip()
                        slugs.append((slug, clean_name))

            return slugs

        except Exception as e:
            logger.exception(f"PhoneHero: fel vid slug-hämtning: {e}")
            return []

    # ─── Steg 2: hämta priser för en specifik modell ────────────────────────

    async def _fetch_model_prices(
        self, client: httpx.AsyncClient, slug: str, model_name: str
    ) -> List[Dict]:
        """Hämta priser för en modell via ?model={slug}."""
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

            # working_model är en Livewire-nästlad lista: [item, {'s': 'arr'}]
            wm = working_model[0] if isinstance(working_model, list) else working_model
            sizes = wm.get("sizes", [])
            if not sizes:
                return []

            # sizes är nästlad: [[{size_obj}, {'s': 'arr'}], ...]
            sizes_list = sizes[0] if isinstance(sizes[0], list) else sizes

            prices = []
            for size_entry in sizes_list:
                if not isinstance(size_entry, list) or not size_entry:
                    continue
                size = size_entry[0]
                storage_str = size.get("name", "")  # e.g., "128 GB" eller "1 TB"
                base_price = size.get("price", 0)

                if not base_price or base_price <= 0:
                    continue

                storage_gb = self._parse_storage(storage_str)

                prices.append({
                    "model": model_name,
                    "storage_gb": storage_gb,
                    "condition": "nyskick",  # Basbeloppet = bästa skick
                    "price_sek": int(base_price),
                    "url": f"{SELL_URL}?model={slug}",
                })

            return prices

        except Exception as e:
            logger.debug(f"PhoneHero: fel för {slug}: {e}")
            return []

    # ─── Hjälpmetoder ────────────────────────────────────────────────────────

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
        """Konvertera '128 GB' → 128, '1 TB' → 1024."""
        m = STORAGE_RE.search(storage_str)
        if not m:
            return None
        value = int(m.group(1))
        unit = m.group(2).upper()
        return value * 1024 if unit == "TB" else value
