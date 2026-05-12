"""
Telestore-scraper

Telestore (telestore.se) visar inköpspriser direkt på sin sälj-sida
/salja-mobil/ i formatet "iPhone X Pro Max Upp till 5 640 kr".
Vi hämtar sidan och extraherar alla iPhone-priser med regex.
"""
import httpx
import logging
import re
from typing import List, Dict, Any
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

# Matchar: "iPhone 15 Pro Max Upp till 5 640 kr"
PRICE_PATTERN = re.compile(
    r"(iPhone\s+"
    r"(?:\d+\w*(?:\s+(?:Pro(?:\s+Max)?|Plus|mini))?|SE(?:\s+\d+)?|Air))"
    r"\s+Upp\s+till\s+([\d\s\xa0]+)\s*kr",
    re.I,
)


class TelestoreScraper(BaseScraper):
    retailer_id = "telestore"
    retailer_name = "Telestore"

    async def fetch_prices(self) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(
            timeout=settings.request_timeout_seconds,
            follow_redirects=True,
            headers=HEADERS,
        ) as client:
            try:
                resp = await client.get(SELL_URL)
                resp.raise_for_status()
            except Exception as e:
                logger.error(f"Telestore: kunde inte hämta {SELL_URL}: {e}")
                return []

            soup = BeautifulSoup(resp.text, "lxml")
            text = soup.get_text(" ", strip=True)

            prices = []
            seen = set()

            for model, price_raw in PRICE_PATTERN.findall(text):
                model = model.strip()
                if model in seen:
                    continue
                seen.add(model)

                price_str = price_raw.replace("\xa0", "").replace(" ", "").strip()
                try:
                    price = int(price_str)
                except ValueError:
                    continue

                if price < 100:
                    continue

                prices.append({
                    "model": model,
                    "storage_gb": None,    # Telestore visar maxpris per modell
                    "condition": "nyskick",  # Maxpriset = bästa skick
                    "price_sek": price,
                    "url": SELL_URL,
                })

            logger.info(f"Telestore: {len(prices)} iPhone-priser hämtade")
            return prices
