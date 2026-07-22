#!/usr/bin/env python3
"""Hämta Swappies livepriser och importera dem i Railway.

Pushern återanvänder alltid den ordinarie scrapern och schemavalideringen.
Därmed kan den manuella produktionsvägen inte driva ifrån den
schemalagda körningen eller tyst ignorera nya Swappie-flaggor.
"""
import asyncio
import json
import logging
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.scrapers.swappie import SwappieScraper


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

RAILWAY_URL = "https://cashmyphone-production.up.railway.app"
API_KEY = "banankaka998877665544332211"


async def main() -> None:
    logger.info("Startar Swappie-import med delad scraperlogik...")
    prices = await SwappieScraper().fetch_prices()
    if not prices:
        raise RuntimeError("Swappie returnerade inga normaliserade priser")

    logger.info("Pushar %s priser till Railway...", len(prices))
    async with httpx.AsyncClient(timeout=90) as client:
        response = await client.post(
            f"{RAILWAY_URL}/api/import-prices/swappie",
            headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
            content=json.dumps(prices),
        )
    response.raise_for_status()
    result = response.json()
    logger.info("Klart: %s priser sparade", result["imported"])


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        logger.error("Swappie-importen misslyckades: %s", exc)
        sys.exit(1)
