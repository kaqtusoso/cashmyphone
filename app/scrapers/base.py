import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, FrozenSet, Iterable, Mapping, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from ..models import BuybackPrice, ScraperRun, ScrapeStatusOut
from ..pricing.history import replace_current_buyback_prices

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstrakt basklass för alla återförsäljare-scrapers."""

    retailer_id: str  # t.ex. "swappie"
    retailer_name: str  # t.ex. "Swappie"
    min_models: int = 1
    min_rows: int = 1
    expected_conditions: Optional[FrozenSet[str]] = None
    expected_condition_count: Optional[int] = None
    max_row_drop_fraction: float = 0.35

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

    async def validate_prices(
        self,
        prices: Iterable[Mapping[str, Any]],
        db: AsyncSession,
    ) -> List[Dict[str, Any]]:
        """Fail-closed-validering innan en komplett prislista får ersätta den gamla."""
        rows = [dict(price) for price in prices]
        if len(rows) < self.min_rows:
            raise RuntimeError(
                f"{self.retailer_name}: endast {len(rows)} rader, kräver minst {self.min_rows}"
            )

        models = {str(row.get("model") or "").strip() for row in rows}
        models.discard("")
        if len(models) < self.min_models:
            raise RuntimeError(
                f"{self.retailer_name}: endast {len(models)} modeller, kräver minst {self.min_models}"
            )

        conditions = {str(row.get("condition") or "") for row in rows}
        if self.expected_conditions is not None and conditions != set(self.expected_conditions):
            missing = sorted(set(self.expected_conditions) - conditions)
            unknown = sorted(conditions - set(self.expected_conditions))
            raise RuntimeError(
                f"{self.retailer_name}: oväntat conditionschema; "
                f"saknas={missing[:8]}, okända={unknown[:8]}"
            )
        if (
            self.expected_condition_count is not None
            and len(conditions) < self.expected_condition_count
        ):
            raise RuntimeError(
                f"{self.retailer_name}: endast {len(conditions)} condition-nycklar, "
                f"kräver minst {self.expected_condition_count}"
            )

        logical_rows: Dict[tuple, int] = {}
        logical_urls: Dict[tuple, Optional[str]] = {}
        canonical_rows: Dict[tuple, Dict[str, Any]] = {}
        for row in rows:
            if not row.get("model") or row.get("storage_gb") is None or not row.get("condition"):
                raise RuntimeError(f"{self.retailer_name}: ofullständig prisrad: {row}")
            try:
                price = int(row.get("price_sek"))
            except (TypeError, ValueError) as exc:
                raise RuntimeError(f"{self.retailer_name}: ogiltigt pris: {row}") from exc
            if price < 0:
                raise RuntimeError(f"{self.retailer_name}: negativt pris: {row}")
            key = (
                str(row["model"]).strip().lower(),
                int(row["storage_gb"]),
                str(row["condition"]).strip().lower(),
            )
            previous = logical_rows.get(key)
            if previous is not None and previous != price:
                current_url = str(row.get("url") or "") or None
                if not current_url or logical_urls.get(key) != current_url:
                    raise RuntimeError(
                        f"{self.retailer_name}: motstridiga dubbletter för {key}: {previous}/{price}"
                    )
                # Vissa officiella kalkyler innehåller samma lagring två gånger.
                # Deras klient väljer första/högsta observerbara bud; kanonisera
                # identiska käll-URL:er på samma sätt innan import.
                if price > previous:
                    logical_rows[key] = price
                    canonical_rows[key] = row
                continue
            logical_rows[key] = price
            logical_urls[key] = str(row.get("url") or "") or None
            canonical_rows[key] = row

        current_count = await db.scalar(
            select(func.count(BuybackPrice.id)).where(
                func.lower(BuybackPrice.retailer) == self.retailer_id.lower(),
                BuybackPrice.is_active.is_(True),
            )
        ) or 0
        unique_count = len(logical_rows)
        if current_count and unique_count < current_count * (1 - self.max_row_drop_fraction):
            drop = 1 - (unique_count / current_count)
            raise RuntimeError(
                f"{self.retailer_name}: prislistan krympte {drop:.1%} "
                f"({current_count} → {unique_count}); import stoppad"
            )
        return list(canonical_rows.values())

    async def run(self, db: AsyncSession) -> ScrapeStatusOut:
        """Kör scraping och spara/uppdatera priser i databasen."""
        run = ScraperRun(retailer=self.retailer_id, started_at=datetime.utcnow())
        db.add(run)
        await db.commit()

        try:
            prices = await self.fetch_prices()

            prices = await self.validate_prices(prices, db)

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
