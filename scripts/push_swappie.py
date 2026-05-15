#!/usr/bin/env python3
"""
Lokal Swappie-pusher — kör scrapern på din Mac och pushar priserna till Railway.

Kör manuellt:
    python scripts/push_swappie.py

Eller lägg till i crontab för daglig körning (kl 06:00):
    0 6 * * * cd /Users/pascalbrjansson/Documents/Claude/Projects/CashMyPhone && python scripts/push_swappie.py >> /tmp/swappie_push.log 2>&1
"""
import asyncio
import json
import logging
import sys
import os

import httpx

# Lägg till projektets rot i Python-sökvägen
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

RAILWAY_URL = "https://cashmyphone-production.up.railway.app"
API_KEY = "banankaka998877665544332211"


async def main():
    logger.info("🚀 Startar lokal Swappie-scraper...")

    # Importera och kör Swappie-scrapern direkt
    from app.scrapers.swappie import SwappieScraper

    scraper = SwappieScraper()
    try:
        prices = await scraper.fetch_prices()
    except Exception as e:
        logger.error(f"Scraper kraschade: {e}")
        sys.exit(1)

    if not prices:
        logger.warning("Inga priser hämtades — avbryter.")
        sys.exit(1)

    logger.info(f"✅ Hämtade {len(prices)} priser — pushar till Railway...")

    # Pusha till Railway-API:et
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{RAILWAY_URL}/api/import-prices/swappie",
            headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
            content=json.dumps(prices),
        )
        if resp.status_code == 200:
            result = resp.json()
            logger.info(f"🎉 Klart! {result['imported']} priser sparade i Railway-databasen.")
        else:
            logger.error(f"API-fel {resp.status_code}: {resp.text}")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
