import unittest
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.database import Base
from app.pricing.history import replace_current_buyback_prices
from app.scrapers.base import BaseScraper


class DemoScraper(BaseScraper):
    retailer_id = "demo"
    retailer_name = "Demo"
    min_models = 1
    min_rows = 1
    expected_conditions = frozenset({"good", "broken"})

    async def fetch_prices(self):
        return []


def row(model, condition, price=1000):
    return {
        "model": model,
        "storage_gb": 128,
        "condition": condition,
        "price_sek": price,
    }


class ScraperValidationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    async def asyncTearDown(self):
        await self.engine.dispose()

    async def test_unknown_or_missing_condition_schema_is_rejected(self):
        async with self.sessions() as db:
            with self.assertRaisesRegex(RuntimeError, "conditionschema"):
                await DemoScraper().validate_prices([row("iPhone 13", "good")], db)

    async def test_conflicting_duplicate_is_rejected(self):
        rows = [
            row("iPhone 13", "good", 1000),
            row("iPhone 13", "good", 900),
            row("iPhone 13", "broken", 100),
        ]
        async with self.sessions() as db:
            with self.assertRaisesRegex(RuntimeError, "motstridiga dubbletter"):
                await DemoScraper().validate_prices(rows, db)

    async def test_large_partial_snapshot_is_rejected(self):
        current = [
            row(f"iPhone {index}", condition, 1000 - index)
            for index in range(10)
            for condition in ("good", "broken")
        ]
        partial = [
            row(f"iPhone {index}", condition, 1000 - index)
            for index in range(3)
            for condition in ("good", "broken")
        ]
        async with self.sessions() as db:
            await replace_current_buyback_prices(
                db,
                retailer="demo",
                prices=current,
                captured_at=datetime.now(UTC).replace(tzinfo=None),
                source="test",
            )
            await db.commit()
            with self.assertRaisesRegex(RuntimeError, "krympte"):
                await DemoScraper().validate_prices(partial, db)


if __name__ == "__main__":
    unittest.main()
