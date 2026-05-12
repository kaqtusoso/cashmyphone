import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from ..models import BuybackPrice, ScraperRun, ScrapeStatusOut

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

            # Markera gamla priser som inaktiva
            await db.execute(
                update(BuybackPrice)
                .where(BuybackPrice.retailer == self.retailer_id)
                .values(is_active=False)
            )

            # Lägg till nya priser
            for p in prices:
                db.add(BuybackPrice(
                    retailer=self.retailer_id,
                    model=p["model"],
                    storage_gb=p.get("storage_gb"),
                    condition=p.get("condition"),
                    price_sek=p["price_sek"],
                    currency="SEK",
                    url=p.get("url"),
                    scraped_at=datetime.utcnow(),
                    is_active=True,
                ))

            run.status = "success"
            run.prices_found = len(prices)
            run.finished_at = datetime.utcnow()
            await db.commit()

            logger.info(f"✅ {self.retailer_name}: {len(prices)} priser sparade")
            return ScrapeStatusOut(retailer=self.retailer_id, status="success",
                                   message=f"{len(prices)} priser hämtade", prices_found=len(prices))

        except Exception as e:
            logger.exception(f"❌ {self.retailer_name} scraping misslyckades: {e}")
            run.status = "error"
            run.error_message = str(e)
            run.finished_at = datetime.utcnow()
            await db.commit()
            return ScrapeStatusOut(retailer=self.retailer_id, status="error",
                                   message=str(e))
