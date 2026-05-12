import logging
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import ScrapeStatusOut
from .swappie import SwappieScraper
from .phonehero import PhoneHeroScraper
from .happyphone import HappyPhoneScraper
from .fixmyphone import FixMyPhoneScraper
from .telestore import TelestoreScraper
from .teknikcentralen import TeknikcentralenScraper

logger = logging.getLogger(__name__)

SCRAPERS = {
    "swappie": SwappieScraper,
    "phonehero": PhoneHeroScraper,
    "happyphone": HappyPhoneScraper,
    "fixmyphone": FixMyPhoneScraper,
    "telestore": TelestoreScraper,
    "teknikcentralen": TeknikcentralenScraper,
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


async def run_all_scrapers(db: AsyncSession) -> List[ScrapeStatusOut]:
    """Kör alla scrapers och returnera status för varje."""
    results = []
    for retailer_id, scraper_class in SCRAPERS.items():
        logger.info(f"→ Startar {scraper_class().retailer_name}...")
        result = await scraper_class().run(db)
        results.append(result)
    return results
