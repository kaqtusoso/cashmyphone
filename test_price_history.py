import unittest
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.database import Base
from app.models import BuybackPrice, BuybackPriceHistory, PriceSnapshot
from app.pricing.history import replace_current_buyback_prices


class PriceHistoryTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)
        self.start = datetime(2026, 7, 16, 8, 0, 0)

    async def asyncTearDown(self):
        await self.engine.dispose()

    @staticmethod
    def prices(first_price=5000, include_second=True, include_third=False):
        rows = [
            {
                "model": "iPhone 15 Pro",
                "storage_gb": 256,
                "condition": "good",
                "price_sek": first_price,
                "url": "https://example.test/15-pro",
            }
        ]
        if include_second:
            rows.append(
                {
                    "model": "iPhone 14",
                    "storage_gb": 128,
                    "condition": "good",
                    "price_sek": 3200,
                }
            )
        if include_third:
            rows.append(
                {
                    "model": "iPhone 16",
                    "storage_gb": 128,
                    "condition": "good",
                    "price_sek": 6100,
                }
            )
        return rows

    async def test_unchanged_snapshot_does_not_duplicate_history_rows(self):
        async with self.sessions() as db:
            first = await replace_current_buyback_prices(
                db,
                retailer="demo",
                prices=self.prices(),
                captured_at=self.start,
                source="scraper",
            )
            second = await replace_current_buyback_prices(
                db,
                retailer="demo",
                prices=self.prices(),
                captured_at=self.start + timedelta(hours=6),
                source="scraper",
            )
            await db.commit()

            history_count = await db.scalar(select(func.count(BuybackPriceHistory.id)))
            snapshot_count = await db.scalar(select(func.count(PriceSnapshot.id)))
            current_count = await db.scalar(select(func.count(BuybackPrice.id)))

        self.assertEqual(first.added, 2)
        self.assertEqual(second.unchanged, 2)
        self.assertEqual(history_count, 2)
        self.assertEqual(snapshot_count, 2)
        self.assertEqual(current_count, 2)

    async def test_changed_removed_and_added_prices_create_periods(self):
        async with self.sessions() as db:
            await replace_current_buyback_prices(
                db,
                retailer="demo",
                prices=self.prices(),
                captured_at=self.start,
                source="scraper",
            )
            changed_at = self.start + timedelta(days=1)
            stats = await replace_current_buyback_prices(
                db,
                retailer="demo",
                prices=self.prices(
                    first_price=4800,
                    include_second=False,
                    include_third=True,
                ),
                captured_at=changed_at,
                source="scraper",
            )
            await db.commit()

            periods = (
                await db.execute(
                    select(BuybackPriceHistory).order_by(BuybackPriceHistory.id)
                )
            ).scalars().all()
            open_periods = [row for row in periods if row.valid_to is None]

        self.assertEqual((stats.added, stats.changed, stats.removed, stats.unchanged), (1, 1, 1, 0))
        self.assertEqual(len(periods), 4)
        self.assertEqual(len(open_periods), 2)
        self.assertEqual(
            [row.price_sek for row in periods if row.model == "iPhone 15 Pro"],
            [5000, 4800],
        )
        self.assertEqual(periods[0].valid_to, changed_at)

    async def test_existing_latest_only_rows_are_bootstrapped_before_replacement(self):
        async with self.sessions() as db:
            db.add(
                BuybackPrice(
                    retailer="demo",
                    model="iPhone 15 Pro",
                    storage_gb=256,
                    condition="good",
                    price_sek=5000,
                    scraped_at=self.start,
                    is_active=True,
                )
            )
            await db.commit()

            await replace_current_buyback_prices(
                db,
                retailer="demo",
                prices=self.prices(first_price=4900, include_second=False),
                captured_at=self.start + timedelta(days=1),
                source="import",
            )
            await db.commit()

            snapshots = (
                await db.execute(select(PriceSnapshot).order_by(PriceSnapshot.id))
            ).scalars().all()
            periods = (
                await db.execute(
                    select(BuybackPriceHistory).order_by(BuybackPriceHistory.valid_from)
                )
            ).scalars().all()

        self.assertEqual([row.source for row in snapshots], ["bootstrap", "import"])
        self.assertEqual([row.price_sek for row in periods], [5000, 4900])
        self.assertEqual(periods[0].valid_to, self.start + timedelta(days=1))
