"""
HappyPhone-scraper – WordPress + WooCommerce.

HappyPhone (happyphone.se) har en inköpssida på /shop/sell/ där de
listar alla modeller de köper in med "Upp till X kr"-priser. Vi bläddrar
igenom alla sidorna och hämtar max-priset per iPhone-modell.

Obs: HappyPhone visar ett enda maxpris per modell (inte per lagring).
     Priset beror sedan på skick och lagring, men basbeloppet är det
     bästa erbjudandet (bästa skick + largest storage).
"""
import httpx
import logging
import re
import asyncio
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from .base import BaseScraper
from ..config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://happyphone.se"
SELL_URL = f"{BASE_URL}/shop/sell/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "sv-SE,sv;q=0.9",
}

MODEL_RE = re.compile(
    r"iPhone\s+(?:\d+\w*(?:\s+(?:Pro(?:\s+Max)?|Plus|mini))?|SE(?:\s+(?:\d+|2020|2022))?)",
    re.I,
)
PRICE_RE = re.compile(r"([\d\s\xa0]{2,8})\s*kr")


class HappyPhoneScraper(BaseScraper):
    retailer_id = "happyphone"
    retailer_name = "HappyPhone"

    async def fetch_prices(self) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(
            timeout=settings.request_timeout_seconds,
            follow_redirects=True,
            headers=HEADERS,
        ) as client:
            prices = await self._scrape_sell_listing(client)
            if not prices:
                logger.warning("HappyPhone: inga priser från listningssidan")
            return prices

    async def _scrape_sell_listing(self, client: httpx.AsyncClient) -> List[Dict]:
        """Bläddra igenom /shop/sell/ och hämta alla iPhone-inköpspriser."""
        prices = []
        seen_models = set()

        for page in range(1, 15):
            url = f"{SELL_URL}page/{page}/" if page > 1 else SELL_URL
            try:
                resp = await client.get(url)
                if resp.status_code == 404:
                    break
                resp.raise_for_status()
            except Exception as e:
                logger.debug(f"HappyPhone sida {page}: {e}")
                break

            soup = BeautifulSoup(resp.text, "lxml")
            cards = soup.find_all("li", class_="sellCard")

            if not cards:
                break

            for card in cards:
                price_data = self._parse_card(card, url)
                if price_data:
                    key = price_data["model"]
                    if key not in seen_models:
                        seen_models.add(key)
                        prices.append(price_data)

            await asyncio.sleep(0.3)

        logger.info(f"HappyPhone: {len(prices)} iPhone-modeller hittade")
        return prices

    def _parse_card(self, card: BeautifulSoup, page_url: str) -> Optional[Dict]:
        """Extrahera modellnamn och maxpris från ett produktkort."""
        # Produktnamn från img alt-text: "sälj begagnad iPhone 15 Pro"
        img = card.find("img")
        alt = img.get("alt", "") if img else ""
        product_name = re.sub(r"^sälj\s+begagnad\s+", "", alt, flags=re.I).strip()

        if not product_name or "iPhone" not in product_name:
            return None

        # Maxpris från <p class="maxPrice">Upp till X kr</p>
        price_p = card.find("p", class_="maxPrice")
        if not price_p:
            return None

        price_text = price_p.get_text(strip=True)
        price_m = PRICE_RE.search(price_text)
        if not price_m:
            return None

        price_str = price_m.group(1).replace("\xa0", "").replace(" ", "").strip()
        try:
            price = int(price_str)
        except ValueError:
            return None

        if price < 100:
            return None

        # Normalisera modellnamn
        model_m = MODEL_RE.search(product_name)
        model = model_m.group(0).strip() if model_m else product_name

        # Produktsidans URL
        link = card.find("a", class_="woocommerce-loop-product__link")
        product_url = link["href"] if link else page_url

        return {
            "model": model,
            "storage_gb": None,    # HappyPhone visar maxpris, inte per lagring
            "condition": "nyskick",  # "Upp till"-priset = bästa skick
            "price_sek": price,
            "url": product_url,
        }
