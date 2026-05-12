"""
Swappie-scraper – Playwright + direkt REST API.

Swappie har ett öppet API på /api/sell/api/v3/prices/ som returnerar
inköpspriser per modell, lagring och skick. API:et är Cloudflare-skyddat
och kräver en aktiv browser-session. Strategi:

  1. Starta Playwright och ladda säljsidan EN gång (Cloudflare-bypass)
  2. Anropa API:et via JavaScript fetch() inifrån browser-kontexten
     – alla modeller hämtas parallellt med Promise.all i batchar om 6
  3. Parsa svaret flexibelt och returnera priser per skick

Resultat: ~1-2 min istället för ~5+ min med sidnavigering.
"""
import asyncio
import logging
import json
import re
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright, TimeoutError as PWTimeout
from .base import BaseScraper
from ..config import settings

logger = logging.getLogger(__name__)

SELL_URL = "https://swappie.com/se/salj-din-iphone/"
API_PATH = "/api/sell/api/v3/prices/"

IPHONE_MODELS = [
    "iPhone 17 Pro Max", "iPhone 17 Pro", "iPhone 17 Plus", "iPhone 17",
    "iPhone 16 Pro Max", "iPhone 16 Pro", "iPhone 16 Plus", "iPhone 16",
    "iPhone 15 Pro Max", "iPhone 15 Pro", "iPhone 15 Plus", "iPhone 15",
    "iPhone 14 Pro Max", "iPhone 14 Pro", "iPhone 14 Plus", "iPhone 14",
    "iPhone 13 Pro Max", "iPhone 13 Pro", "iPhone 13 mini", "iPhone 13",
    "iPhone 12 Pro Max", "iPhone 12 Pro", "iPhone 12 mini", "iPhone 12",
    "iPhone 11 Pro Max", "iPhone 11 Pro", "iPhone 11",
    "iPhone SE (3rd generation)", "iPhone SE (2nd generation)",
    "iPhone XS Max", "iPhone XS", "iPhone XR",
]

ALL_STORAGES = ["64GB", "128GB", "256GB", "512GB", "1TB"]

CONDITION_MAP = {
    "a+": "nyskick", "a": "nyskick",
    "b+": "nyskick", "b": "normalt_sliten",
    "c": "mycket_sliten", "d": "mycket_sliten",
    "like_new": "nyskick", "pristine": "nyskick", "excellent": "nyskick",
    "very_good": "nyskick",
    "good": "normalt_sliten",
    "fair": "mycket_sliten", "acceptable": "mycket_sliten", "poor": "mycket_sliten",
    "som ny": "nyskick",
    "bra skick": "normalt_sliten", "bra": "normalt_sliten",
    "godkänt": "mycket_sliten",
}

STORAGE_RE = re.compile(r"(\d+)\s*(GB|TB)", re.I)


class SwappieScraper(BaseScraper):
    retailer_id = "swappie"
    retailer_name = "Swappie"

    async def fetch_prices(self) -> List[Dict[str, Any]]:
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
            page = await context.new_page()

            try:
                logger.info("Swappie: laddar säljsida för Cloudflare-bypass...")
                await page.goto(SELL_URL, wait_until="networkidle", timeout=60000)
                await asyncio.sleep(2)

                logger.info(f"Swappie: anropar API för {len(IPHONE_MODELS)} modeller...")
                results = await page.evaluate(self._build_js_fetcher())

                if not results:
                    logger.warning("Swappie: inga svar från API")
                    return []

                first_ok = next((r for r in results if r and r.get("data")), None)
                if first_ok:
                    logger.info(
                        f"Swappie API-svar exempel ('{first_ok['model']}'): "
                        f"{json.dumps(first_ok['data'])[:400]}"
                    )

                for result in results:
                    if not result or not result.get("data"):
                        continue
                    extracted = self._parse_response(result["data"], result["model"])
                    prices.extend(extracted)

            except PWTimeout:
                logger.warning("Swappie: timeout – Cloudflare blockerade troligtvis")
            except Exception as e:
                logger.exception(f"Swappie: oväntat fel: {e}")
            finally:
                await browser.close()

        logger.info(f"Swappie: {len(prices)} priser hämtade")
        return prices

    def _build_js_fetcher(self) -> str:
        models_json = json.dumps(IPHONE_MODELS)
        storages_json = json.dumps(ALL_STORAGES)
        return f"""
        async () => {{
            const models = {models_json};
            const storages = {storages_json};
            const storagesParam = encodeURIComponent(JSON.stringify(storages));
            const BATCH = 6;
            const allResults = [];

            for (let i = 0; i < models.length; i += BATCH) {{
                const batch = models.slice(i, i + BATCH);
                const batchResults = await Promise.all(
                    batch.map(async (model) => {{
                        try {{
                            const url = `{API_PATH}?model_name=${{encodeURIComponent(model)}}&country=SE&storages=${{storagesParam}}`;
                            const resp = await fetch(url, {{
                                headers: {{
                                    'Accept': 'application/json',
                                    'X-Requested-With': 'XMLHttpRequest'
                                }}
                            }});
                            if (!resp.ok) return {{model, data: null, status: resp.status}};
                            return {{model, data: await resp.json()}};
                        }} catch(e) {{
                            return {{model, data: null, error: e.message}};
                        }}
                    }})
                );
                allResults.push(...batchResults);
                await new Promise(r => setTimeout(r, 400));
            }}
            return allResults;
        }}
        """

    def _parse_response(self, data: Any, model_name: str) -> List[Dict]:
        prices = []
        url = SELL_URL

        if isinstance(data, list):
            for item in data:
                prices.extend(self._extract_entry(item, model_name, url))
        elif isinstance(data, dict):
            items = (
                data.get("prices") or data.get("grades") or
                data.get("variants") or data.get("items") or
                data.get("results") or []
            )
            if isinstance(items, list):
                for item in items:
                    prices.extend(self._extract_entry(item, model_name, url))
            else:
                prices.extend(self._extract_entry(data, model_name, url))

        return prices

    def _extract_entry(self, item: Any, model_name: str, url: str) -> List[Dict]:
        if not isinstance(item, dict):
            return []

        results = []

        storage_raw = (
            item.get("storage") or item.get("storage_gb") or
            item.get("capacity") or item.get("size") or ""
        )
        storage_gb = self._parse_storage(str(storage_raw)) if storage_raw else None

        grade_raw = str(
            item.get("grade") or item.get("condition") or
            item.get("quality") or item.get("state") or ""
        ).lower()
        condition = CONDITION_MAP.get(grade_raw, "normalt_sliten")

        price_raw = (
            item.get("price") or item.get("amount") or
            item.get("buyback_price") or item.get("value") or 0
        )
        try:
            price = int(float(str(price_raw).replace(",", ".")))
        except (ValueError, TypeError):
            price = 0

        if 100 < price < 50000:
            results.append({
                "model": model_name,
                "storage_gb": storage_gb,
                "condition": condition,
                "price_sek": price,
                "url": url,
            })

        nested_grades = item.get("grades") or {}
        if isinstance(nested_grades, dict):
            for grade_key, grade_val in nested_grades.items():
                g_condition = CONDITION_MAP.get(grade_key.lower(), "normalt_sliten")
                if isinstance(grade_val, dict):
                    g_price_raw = grade_val.get("price") or grade_val.get("amount") or 0
                elif isinstance(grade_val, (int, float)):
                    g_price_raw = grade_val
                else:
                    continue
                try:
                    g_price = int(float(g_price_raw))
                    if 100 < g_price < 50000:
                        results.append({
                            "model": model_name,
                            "storage_gb": storage_gb,
                            "condition": g_condition,
                            "price_sek": g_price,
                            "url": url,
                        })
                except (ValueError, TypeError):
                    pass

        return results

    def _parse_storage(self, text: str) -> Optional[int]:
        m = STORAGE_RE.search(text)
        if not m:
            return None
        val, unit = int(m.group(1)), m.group(2).upper()
        return val * 1024 if unit == "TB" else val
