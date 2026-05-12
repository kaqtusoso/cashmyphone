"""
FixMyPhone-scraper – Playwright-baserad.

FixMyPhone (salja.fixmyphone.se) beräknar inköpspriser dynamiskt i browsern
via ett custom JS-kalkylverktyg (#estimatePrice / #estimateBlock).
Priserna är INTE tillgängliga via REST API eller statisk HTML.

Flöde per modell:
  1. Navigera till modellsidan (t.ex. /salja/iphone-15-pro/)
  2. Välj lagring (1TB → 128 GB) och skick "Som ny" / "Mycket bra" etc.
  3. Välj "Ja" / "Nej" på övriga frågor (bästa möjliga skick)
  4. Läs av priset från #estimatePrice-elementet

Modell-slugar hämtas från FixMyPhones navigation.
"""
import asyncio
import logging
import re
from typing import List, Dict, Any
from playwright.async_api import async_playwright, TimeoutError as PWTimeout
from .base import BaseScraper
from ..config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://salja.fixmyphone.se"
NAV_URL = "https://fixmyphone.se"

# Lagringsvärden → select index (0=1TB, 1=512GB, 2=256GB, 3=128GB)
STORAGE_OPTIONS = [
    (0, 1024),   # 1TB
    (1, 512),    # 512 GB
    (2, 256),    # 256 GB
    (3, 128),    # 128 GB
    (4, 64),     # 64 GB (äldre modeller)
]

# Välj bästa möjliga skick för alla selects
BEST_CONDITION_SELECTIONS = {
    "condition": "like_new",   # Som ny
    "isWorking": "1",          # Fungerar
    "isDisplay": "1",          # Skärm ok
    "isCracked": "0",          # Ej sprucken
    "isWaterDamaged": "0",     # Ej vattenskadad
    "isBattery": "1",          # Bra batteri
    "hasBox": "0",             # Ingen låda (konservativt)
}


class FixMyPhoneScraper(BaseScraper):
    retailer_id = "fixmyphone"
    retailer_name = "FixMyPhone"

    async def fetch_prices(self) -> List[Dict[str, Any]]:
        prices = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=settings.playwright_headless,
                args=["--no-sandbox", "--disable-setuid-sandbox"],
            )
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                locale="sv-SE",
            )

            try:
                # Hämta alla modell-slugar från navigationen
                model_slugs = await self._get_model_slugs(context)
                logger.info(f"FixMyPhone: {len(model_slugs)} iPhone-modeller hittade")

                for model_name, slug in model_slugs:
                    model_prices = await self._scrape_model(context, model_name, slug)
                    prices.extend(model_prices)
                    await asyncio.sleep(0.5)

            except Exception as e:
                logger.exception(f"FixMyPhone: oväntat fel: {e}")
            finally:
                await browser.close()

        return prices

    async def _get_model_slugs(self, context) -> List[tuple]:
        """Hämta iPhone-modeller och deras slug-URLs från navigationen."""
        page = await context.new_page()
        slugs = []
        try:
            await page.goto(NAV_URL, wait_until="domcontentloaded", timeout=30000)
            links = await page.eval_on_selector_all(
                "a[href*='salja.fixmyphone.se/salja/iphone']",
                "els => els.map(e => [e.textContent.trim(), e.href])"
            )
            seen = set()
            for text, href in links:
                m = re.search(r"/salja/(iphone[^/]+)/?$", href)
                if m:
                    slug = m.group(1)
                    # Rensa modellnamn
                    model = re.sub(r"^Sälj\s+", "", text, flags=re.I).strip()
                    if slug not in seen and model:
                        seen.add(slug)
                        slugs.append((model, slug))
        except Exception as e:
            logger.debug(f"FixMyPhone slug-hämtning: {e}")
        finally:
            await page.close()
        return slugs

    async def _scrape_model(self, context, model_name: str, slug: str) -> List[Dict]:
        """Scrapa priser för en modell (alla tillgängliga lagringsstorlekar)."""
        url = f"{BASE_URL}/salja/{slug}/"
        prices = []

        page = await context.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)

            # Sätt alla skick-selects till bästa värde
            for select_name, value in BEST_CONDITION_SELECTIONS.items():
                try:
                    await page.select_option(
                        f'select[name="{select_name}"]', value, timeout=2000
                    )
                except Exception:
                    pass  # Selecten kanske inte finns för denna modell

            # Hämta pris för varje lagringsalternativ
            storage_select = page.locator('select:not([name])')
            count = await storage_select.count()

            if count == 0:
                # Kanske en enda lagringsvariant utan select
                price = await self._read_price(page)
                if price:
                    prices.append({
                        "model": model_name,
                        "storage_gb": None,
                        "condition": "nyskick",
                        "price_sek": price,
                        "url": url,
                    })
            else:
                options = await storage_select.first.locator("option").all()
                for i, opt in enumerate(options):
                    opt_text = await opt.inner_text()
                    storage_gb = self._parse_storage(opt_text)

                    await storage_select.first.select_option(index=i)
                    await page.wait_for_timeout(400)

                    price = await self._read_price(page)
                    if price and price > 100:
                        prices.append({
                            "model": model_name,
                            "storage_gb": storage_gb,
                            "condition": "nyskick",
                            "price_sek": price,
                            "url": url,
                        })

        except PWTimeout:
            logger.debug(f"FixMyPhone: timeout för {slug}")
        except Exception as e:
            logger.debug(f"FixMyPhone: fel för {slug}: {e}")
        finally:
            await page.close()

        return prices

    async def _read_price(self, page) -> int | None:
        """Läs priset från #estimatePrice-elementet."""
        try:
            await page.wait_for_selector("#estimatePrice", timeout=3000)
            price_text = await page.locator("#estimatePrice").inner_text()
            m = re.search(r"([\d\s\xa0]+)", price_text.replace("\xa0", " "))
            if m:
                price_str = m.group(1).replace(" ", "").strip()
                return int(price_str) if price_str.isdigit() else None
        except Exception:
            pass
        return None

    def _parse_storage(self, text: str) -> int | None:
        m = re.search(r"(\d+)\s*(GB|TB)", text, re.I)
        if not m:
            return None
        val, unit = int(m.group(1)), m.group(2).upper()
        return val * 1024 if unit == "TB" else val
