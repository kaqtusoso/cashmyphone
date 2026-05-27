"""
Fixiphone-scraper.

Fixiphone har sin salj-din-mobil-modell hardkodad i HTML. Varje modellkort
innehaller baspris per lagring och fragornas procentavdrag. Deras JS visar ett
intervall vid skador:

  ovre = baspris - baspris / 100 * avdrag
  nedre = baspris - floor(baspris / 70) * avdrag

Vi lagrar den nedre delen av intervallet for att inte overdriva budet.
"""
import itertools
import logging
import re
from typing import Any, Dict, List, Optional

import httpx
from bs4 import BeautifulSoup

from .base import BaseScraper
from ..config import settings

logger = logging.getLogger(__name__)

SELL_URL = "https://www.fixiphone.se/salj-din-mobil/?child-cat=iphone&parent-cat=apple#scroll-section"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "sv-SE,sv;q=0.9,en;q=0.8",
}

DEDUCTION_VALUES = {
    "working": [0, 45],
    "screen_color": [0, 45],
    "wear": [0, 10, 20],
    "glass": [0, 45],
    "critical": [0, 90],
}

ALL_DEDUCTIONS = sorted({
    sum(parts)
    for parts in itertools.product(*DEDUCTION_VALUES.values())
})

STORAGE_RE = re.compile(r"(\d+)\s*GB", re.I)


def _clean_model(name: str) -> str:
    name = re.sub(r"\s+", " ", name or "").strip()
    name = name.replace("Pro max", "Pro Max").replace("plus", "Plus")
    name = name.replace("pro", "Pro")
    name = name.replace("Mini", "mini")
    name = name.replace("Generation 2", "(2020)")
    return name


def _parse_storage(text: str) -> Optional[int]:
    match = STORAGE_RE.search(text or "")
    if not match:
        return None
    storage = int(match.group(1))
    # Fixiphone har en synlig typo for iPhone 17 Pro Max: "246GB".
    if storage == 246:
        return 256
    # Deras 1TB visas som 1000GB, men API:t använder 1024 precis som övriga scrapers.
    return 1024 if storage == 1000 else storage


def _lower_bound_price(base_price: int, deduction: int) -> int:
    price = base_price - ((base_price // 70) * deduction)
    return max(0, int(price))


class FixiphoneScraper(BaseScraper):
    retailer_id = "fixiphone"
    retailer_name = "Fixiphone"

    async def fetch_prices(self) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(
            timeout=settings.request_timeout_seconds,
            follow_redirects=True,
            headers=HEADERS,
        ) as client:
            resp = await client.get(SELL_URL)
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")
        cards = soup.select(".popupInformation .pro-details")

        prices: List[Dict[str, Any]] = []
        for card in cards:
            model_input = card.select_one('input[name="product-name"]')
            model_name = _clean_model(model_input.get("value", "") if model_input else "")
            if not model_name.startswith("iPhone"):
                continue

            for button in card.select(".product-price"):
                base_price = int(button.get("data-price") or 0)
                storage_gb = _parse_storage(button.get_text(" ", strip=True))
                if not base_price or not storage_gb:
                    continue

                for deduction in ALL_DEDUCTIONS:
                    prices.append({
                        "model": model_name,
                        "storage_gb": storage_gb,
                        "condition": f"d{deduction}",
                        "price_sek": _lower_bound_price(base_price, deduction),
                        "url": SELL_URL,
                    })

        logger.info(f"Fixiphone: {len(prices)} priser")
        return prices
