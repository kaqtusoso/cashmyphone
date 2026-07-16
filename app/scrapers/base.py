import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import ScraperRun, ScrapeStatusOut
from ..pricing.history import replace_current_buyback_prices

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstrakt basklass för alla återförsäljare-scrapers."""

    retailer_id: str  # t.ex. "swappie"
    retailer_name: str  # t.ex. "Swappie"

    @abstractmethod
    async def fetch_prices(self) -> List[Dict[str, Any]]:
        """
        Hämta inköpspriser.
        Returnerar lista med dicts:
          {
            "model": "iPhone 15 Pro",
            "storage_gb": 256,
            "condition": "utmärkt",
            "price_sek": 7500,
            "url": "https://..."
          }
        """
        ...

    async def run(self, db: AsyncSession) -> ScrapeStatusOut:
        """Kör scraping och spara/uppdatera priser i databasen."""
        run = ScraperRun(retailer=self.retailer_id, started_at=datetime.utcnow())
        db.add(run)
        await db.commit()

        try:
            prices = await self.fetch_prices()

            if not prices:
                run.status = "error"
                run.error_message = "Inga priser hittades"
                run.finished_at = datetime.utcnow()
                await db.commit()
                return ScrapeStatusOut(retailer=self.retailer_id, status="error",
                                       message="Inga priser hittades")

            captured_at = datetime.utcnow()
            snapshot = await replace_current_buyback_prices(
                db,
                retailer=self.retailer_id,
                prices=prices,
                captured_at=captured_at,
                source="scraper",
            )

            run.status = "success"
            run.prices_found = len(prices)
            run.finished_at = datetime.utcnow()
            await db.commit()

            logger.info(
                "✅ %s: %s priser sparade (historik +%s, ändrade %s, borttagna %s)",
                self.retailer_name,
                len(prices),
                snapshot.added,
                snapshot.changed,
                snapshot.removed,
            )
            return ScrapeStatusOut(retailer=self.retailer_id, status="success",
                                   message=f"{len(prices)} priser hämtade", prices_found=len(prices))

        except Exception as e:
            logger.exception(f"❌ {self.retailer_name} scraping misslyckades: {e}")
            await db.rollback()
            run.status = "error"
            run.error_message = str(e)
            run.finished_at = datetime.utcnow()
            await db.commit()
            return ScrapeStatusOut(retailer=self.retailer_id, status="error",
                                   message=str(e))
