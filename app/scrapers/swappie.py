"""
Swappie-scraper – Playwright med nätverksinterception.

Swappie (swappie.com/se/salj-din-iphone/) är Cloudflare-skyddad och
renderar priser via JavaScript. Vi använder Playwright för att:
  1. Ladda sidan (Cloudflare klarar sig med headless Chromium + rätt UA)
  2. Intercepta XHR/fetch-anrop för att hitta deras interna pris-API
  3. Interagera med formuläret och läsa priser ur DOM:en

Om XHR-interception misslyckas faller vi tillbaka på DOM-extraktion.
"""
import asyncio
import logging
import re
import json
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright, TimeoutError as PWTimeout, Route
from .base import BaseScraper
from ..config import settings

logger = logging.getLogger(__name__)

SELL_URL = "https://swappie.com/se/salj-din-iphone/"

# Nyckelord som identifierar pris-API-svar
PRICE_API_KEYWORDS = ["price", "valuation", "buyback", "quote", "offer", "pris"]

# iPhone-modeller att söka efter (om ingen dynamisk lista hittas)
FALLBACK_MODELS = [
    "iphone-16-pro-max", "iphone-16-pro", "iphone-16-plus", "iphone-16",
    "iphone-15-pro-max", "iphone-15-pro", "iphone-15-plus", "iphone-15",
    "iphone-14-pro-max", "iphone-14-pro", "iphone-14-plus", "iphone-14",
    "iphone-13-pro-max", "iphone-13-pro", "iphone-13-mini", "iphone-13",
    "iphone-12-pro-max", "iphone-12-pro", "iphone-12-mini", "iphone-12",
    "iphone-se-2022", "iphone-se-2020",
]

STORAGE_RE = re.compile(r"(\d+)\s*(GB|TB)", re.I)
MODEL_RE = re.compile(r"iPhone\s+(?:\d+\w*(?:\s+(?:Pro(?:\s+Max)?|Plus|mini))?|SE(?:\s+\d+)?)", re.I)


class SwappieScraper(BaseScraper):
    retailer_id = "swappie"
    retailer_name = "Swappie"

    def __init__(self):
        self._intercepted: List[Dict] = []

    async def fetch_prices(self) -> List[Dict[str, Any]]:
        self._intercepted = []
        prices = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=settings.playwright_headless,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-blink-features=AutomationControlled",
                ],
            )
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                locale="sv-SE",
                viewport={"width": 1280, "height": 800},
            )

            # Intercepta alla nätverksanrop
            async def on_response(response):
                url = response.url.lower()
                if any(kw in url for kw in PRICE_API_KEYWORDS):
                    try:
                        ct = response.headers.get("content-type", "")
                        if "json" in ct:
                            body = await response.json()
                            self._intercepted.append({"url": response.url, "data": body})
                    except Exception:
                        pass

            context.on("response", on_response)

            page = await context.new_page()
            try:
                logger.info("Swappie: laddar sälj-sidan...")
                await page.goto(SELL_URL, wait_until="networkidle", timeout=60000)
                await asyncio.sleep(3)

                # Steg 1: försök extrahera modell-lista från sidan
                model_links = await self._extract_model_links(page)

                if model_links:
                    # Steg 2a: navigera till varje modellsida och hämta priser
                    for href, model_name in model_links[:30]:
                        model_prices = await self._scrape_model_page(page, href, model_name)
                        prices.extend(model_prices)
                        await asyncio.sleep(1)
                else:
                    # Steg 2b: försök med interceptade API-svar
                    prices = self._parse_intercepted(self._intercepted)

                # Om inget hittat, försök med kända modell-slugar
                if not prices:
                    prices = await self._try_model_slugs(page)

            except PWTimeout:
                logger.warning("Swappie: timeout – Cloudflare blockerade troligen")
            except Exception as e:
                logger.exception(f"Swappie: oväntat fel: {e}")
            finally:
                await browser.close()

        logger.info(f"Swappie: {len(prices)} priser hämtade")
        return prices

    # ─── Sidnavigering ───────────────────────────────────────────────────────

    async def _extract_model_links(self, page) -> List[tuple]:
        """Hitta länkarna till enskilda iPhone-modellsidor."""
        try:
            links = await page.eval_on_selector_all(
                "a[href*='/se/salj-din-iphone/iphone'], "
                "a[href*='/salj/iphone'], "
                "[data-model] a, .model-card a, .device-card a",
                "els => els.map(e => [e.href, e.textContent.trim()])"
            )
            result = []
            seen = set()
            for href, text in links:
                if href not in seen and "iphone" in href.lower():
                    model = MODEL_RE.search(text)
                    name = model.group(0) if model else text.strip()
                    if name:
                        seen.add(href)
                        result.append((href, name))
            return result
        except Exception as e:
            logger.debug(f"Swappie extract_model_links: {e}")
            return []

    async def _scrape_model_page(self, page, url: str, model_name: str) -> List[Dict]:
        """Navigera till en modellsida och läs ut priser."""
        prices = []
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(1)

            # Kolla interceptade svar från denna sida
            if self._intercepted:
                prices = self._parse_intercepted(self._intercepted[-5:], model_name)
                if prices:
                    return prices

            # Fallback: extrahera priser från DOM
            prices = await self._extract_prices_from_dom(page, model_name, url)
        except Exception as e:
            logger.debug(f"Swappie model page {url}: {e}")
        return prices

    async def _try_model_slugs(self, page) -> List[Dict]:
        """Prova kända modell-slugar direkt."""
        prices = []
        for slug in FALLBACK_MODELS:
            url = f"{SELL_URL}{slug}/"
            try:
                resp = await page.goto(url, wait_until="networkidle", timeout=20000)
                if resp and resp.status == 200:
                    await asyncio.sleep(1)
                    # Kolla interceptade
                    if self._intercepted:
                        found = self._parse_intercepted(self._intercepted[-3:])
                        if found:
                            prices.extend(found)
                            continue
                    # DOM fallback
                    model_name = slug.replace("-", " ").title().replace("Iphone", "iPhone")
                    dom_prices = await self._extract_prices_from_dom(page, model_name, url)
                    prices.extend(dom_prices)
            except Exception:
                pass
            await asyncio.sleep(0.5)
        return prices

    # ─── Prisextraktion ──────────────────────────────────────────────────────

    async def _extract_prices_from_dom(self, page, model_name: str, url: str) -> List[Dict]:
        """Extrahera priser ur DOM:en."""
        prices = []
        try:
            content = await page.content()

            # Sök efter JSON-data inbäddad i sidan
            json_matches = re.findall(
                r'"(?:price|amount|buyback_price|sell_price)"\s*:\s*(\d{3,6})', content
            )
            for price_str in json_matches:
                price = int(price_str)
                if 500 < price < 30000:
                    prices.append({
                        "model": model_name,
                        "price_sek": price,
                        "url": url,
                    })
            if prices:
                # Ta bort dubbletter och behåll unika priser
                seen_prices = set()
                unique = []
                for p in prices:
                    if p["price_sek"] not in seen_prices:
                        seen_prices.add(p["price_sek"])
                        unique.append(p)
                return unique

            # Sök i textnoder
            price_texts = await page.eval_on_selector_all(
                "[class*='price'], [class*='amount'], [data-price]",
                "els => els.map(e => e.innerText || e.getAttribute('data-price'))"
            )
            for txt in price_texts:
                m = re.search(r"(\d{3,6})", str(txt).replace("\xa0", "").replace(" ", ""))
                if m:
                    price = int(m.group(1))
                    if 500 < price < 30000:
                        prices.append({
                            "model": model_name,
                            "price_sek": price,
                            "url": url,
                        })
        except Exception as e:
            logger.debug(f"Swappie DOM-extraktion: {e}")
        return prices

    def _parse_intercepted(
        self, responses: List[Dict], model_name: Optional[str] = None
    ) -> List[Dict]:
        """Parsa interceptade API-svar och extrahera prisdata."""
        prices = []
        for resp in responses:
            data = resp.get("data", {})
            url = resp.get("url", "")
            extracted = self._extract_from_json(data, url, model_name)
            prices.extend(extracted)
        return prices

    def _extract_from_json(
        self, data, url: str, model_name: Optional[str] = None
    ) -> List[Dict]:
        """Rekursivt extrahera prisdata från JSON-struktur."""
        prices = []
        if isinstance(data, list):
            for item in data:
                prices.extend(self._extract_from_json(item, url, model_name))
        elif isinstance(data, dict):
            # Sök efter modell + pris
            name = (
                data.get("model") or data.get("name") or
                data.get("device_name") or data.get("title") or model_name or ""
            )
            price = (
                data.get("price") or data.get("amount") or
                data.get("buyback_price") or data.get("sell_price") or
                data.get("offer_price") or 0
            )
            storage = data.get("storage") or data.get("capacity") or data.get("storage_gb")
            condition = data.get("condition") or data.get("grade")

            if name and price and "iphone" in str(name).lower():
                try:
                    p = int(float(price))
                    if 500 < p < 30000:
                        storage_gb = None
                        if storage:
                            sm = STORAGE_RE.search(str(storage))
                            if sm:
                                val, unit = int(sm.group(1)), sm.group(2).upper()
                                storage_gb = val * 1024 if unit == "TB" else val
                        prices.append({
                            "model": MODEL_RE.search(str(name)).group(0) if MODEL_RE.search(str(name)) else name,
                            "storage_gb": storage_gb,
                            "condition": condition,
                            "price_sek": p,
                            "url": url,
                        })
                except (ValueError, TypeError):
                    pass

            # Rekursera in i nästlade dicts
            for v in data.values():
                if isinstance(v, (dict, list)):
                    prices.extend(self._extract_from_json(v, url, model_name))

        return prices
