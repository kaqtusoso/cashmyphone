"""
FixMyPhone-scraper – Playwright med parallella sidor.

FixMyPhone (salja.fixmyphone.se) beräknar priser dynamiskt i browsern.
Optimering: kör upp till 3 modeller parallellt med asyncio.Semaphore
istället för sekventiellt.
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

BEST_CONDITION_SELECTIONS = {
    "condition": "like_new",
    "isWorking": "1",
    "isDisplay": "1",
    "isCracked": "0",
    "isWaterDamaged": "0",
    "isBattery": "1",
    "hasBox": "0",
}

MAX_CONCURRENT_PAGES = 3


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
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ),
                locale="sv-SE",
            )

            try:
                model_slugs = await self._get_model_slugs(context)
                logger.info(f"FixMyPhone: {len(model_slugs)} modeller hittade, kör parallellt ({MAX_CONCURRENT_PAGES} åt gången)")

                sem = asyncio.Semaphore(MAX_CONCURRENT_PAGES)

                async def scrape_with_sem(model_name: str, slug: str) -> List[Dict]:
                    async with sem:
                        return await self._scrape_model(context, model_name, slug)

                results = await asyncio.gather(
                    *[scrape_with_sem(name, slug) for name, slug in model_slugs],
                    return_exceptions=True,
                )

                for result in results:
                    if isinstance(result, Exception):
                        logger.debug(f"FixMyPhone: modell-fel: {result}")
                    elif result:
                        prices.extend(result)

            except Exception as e:
                logger.exception(f"FixMyPhone: oväntat fel: {e}")
            finally:
                await browser.close()

        logger.info(f"FixMyPhone: {len(prices)} priser hämtade")
        return prices

    async def _get_model_slugs(self, context) -> List[tuple]:
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
        url = f"{BASE_URL}/salja/{slug}/"
        prices = []
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)

            for select_name, value in BEST_CONDITION_SELECTIONS.items():
                try:
                    await page.select_option(f'select[name="{select_name}"]', value, timeout=1500)
                except Exception:
                    pass

            storage_select = page.locator('select:not([name])')
            count = await storage_select.count()

            if count == 0:
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
                    await page.wait_for_timeout(300)
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
        try:
            await page.wait_for_selector("#estimatePrice", timeout=2500)
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
