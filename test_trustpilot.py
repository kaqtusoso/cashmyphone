import unittest

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.database import Base
from app.models import TrustpilotProfile
from app.trustpilot import (
    TRUSTPILOT_RETAILERS,
    TrustpilotScrapeResult,
    get_trustpilot_snapshots,
    parse_review_count,
    refresh_trustpilot_profiles,
)


class TrustpilotCacheTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    async def asyncTearDown(self):
        await self.engine.dispose()

    @staticmethod
    def fetcher(review_counts, errors=None):
        async def fetch():
            return TrustpilotScrapeResult(
                review_counts=review_counts,
                errors=errors or {},
            )

        return fetch

    def test_review_count_parser_accepts_swedish_grouping_spaces(self):
        self.assertEqual(parse_review_count("67\u00a0618"), 67_618)
        self.assertEqual(parse_review_count("14\u202f833"), 14_833)
        self.assertEqual(parse_review_count("42"), 42)
        with self.assertRaises(ValueError):
            parse_review_count("68 tn omdömen")

    async def test_first_refresh_populates_all_retailer_counts(self):
        review_counts = {
            retailer: index + 100
            for index, retailer in enumerate(TRUSTPILOT_RETAILERS)
        }

        async with self.sessions() as db:
            statuses = await refresh_trustpilot_profiles(
                db,
                fetcher=self.fetcher(review_counts),
            )
            count = await db.scalar(select(func.count(TrustpilotProfile.id)))
            swappie = await db.scalar(
                select(TrustpilotProfile).where(
                    TrustpilotProfile.retailer == "swappie"
                )
            )

        self.assertEqual(set(statuses.values()), {"updated"})
        self.assertEqual(count, len(TRUSTPILOT_RETAILERS))
        self.assertEqual(swappie.score, 4.4)
        self.assertEqual(swappie.review_count, 100)

    async def test_failed_refresh_preserves_previous_cached_value(self):
        async with self.sessions() as db:
            db.add(
                TrustpilotProfile(
                    retailer="swappie",
                    domain="swappie.com",
                    profile_url="https://se.trustpilot.com/review/swappie.com",
                    score=4.3,
                    review_count=66_000,
                )
            )
            await db.commit()

            statuses = await refresh_trustpilot_profiles(
                db,
                fetcher=self.fetcher(
                    {"phonehero": 14_900},
                    {"swappie": "blocked"},
                ),
            )
            snapshot = (await get_trustpilot_snapshots(db, ["swappie"]))["swappie"]

        self.assertEqual(statuses["swappie"], "error")
        self.assertEqual(snapshot.score, 4.3)
        self.assertEqual(snapshot.review_count, 66_000)

    async def test_empty_cache_uses_dated_fallback(self):
        async with self.sessions() as db:
            snapshots = await get_trustpilot_snapshots(
                db,
                ["swappie", "unknown"],
            )

        self.assertEqual(snapshots["swappie"].review_count, 67_618)
        self.assertNotIn("unknown", snapshots)


if __name__ == "__main__":
    unittest.main()
