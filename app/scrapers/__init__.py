import asyncio
import logging
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import ScrapeStatusOut
from ..database import AsyncSessionLocal
from .swappie import SwappieScraper
from .phonehero import PhoneHeroScraper
from .renewed import RenewedScraper
from .happyphone import HappyPhoneScraper
from .fixmyphone import FixMyPhoneScraper
from .telestore import TelestoreScraper
from .teknikcentralen import TeknikcentralenScraper
from .fixiphone import FixiphoneScraper
from .fixphonepro import FixPhoneProScraper

logger = logging.getLogger(__name__)

SCRAPERS = {
    "swappie": SwappieScraper,
    "phonehero": PhoneHeroScraper,
    "renewed": RenewedScraper,
    "happyphone": HappyPhoneScraper,
    "fixmyphone": FixMyPhoneScraper,
    "telestore": TelestoreScraper,
    "teknikcentralen": TeknikcentralenScraper,
    "fixiphone": FixiphoneScraper,
    "fixphonepro": FixPhoneProScraper,
}


async def run_scraper(retailer_id: str, db: AsyncSession) -> ScrapeStatusOut:
    """Kör en enskild scraper."""
    scraper_class = SCRAPERS.get(retailer_id.lower())
    if not scraper_class:
        return ScrapeStatusOut(
            retailer=retailer_id,
            status="error",
            message=f"Okänd återförsäljare: {retailer_id}",
        )
    return await scraper_class().run(db)


SCRAPER_TIMEOUT = 120  # sekunder per scraper


async def run_all_scrapers(db: AsyncSession) -> List[ScrapeStatusOut]:
    """Kör alla scrapers parallellt – varje scraper får en egen DB-session."""

    async def run_isolated(retailer_id: str, scraper_class) -> ScrapeStatusOut:
        async with AsyncSessionLocal() as session:
            logger.info(f"→ Startar {scraper_class.retailer_name if hasattr(scraper_class, 'retailer_name') else retailer_id}...")
            return await asyncio.wait_for(
                scraper_class().run(session),
                timeout=SCRAPER_TIMEOUT,
            )

    tasks = [
        run_isolated(rid, cls)
        for rid, cls in SCRAPERS.items()
    ]

    raw_results = await asyncio.gather(*tasks, return_exceptions=True)

    results = []
    for retailer_id, result in zip(SCRAPERS.keys(), raw_results):
        if isinstance(result, Exception):
            logger.error(f"Scraper '{retailer_id}' kraschade: {result}")
            results.append(ScrapeStatusOut(
                retailer=retailer_id,
                status="error",
                message=str(result),
            ))
        else:
            results.append(result)

    return results
