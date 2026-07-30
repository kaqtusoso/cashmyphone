"""Daglig webbläsarhämtning av återförsäljarnas publika Trustpilot-data."""

from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass
from datetime import datetime
import logging
import re
from typing import Optional

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .models import TrustpilotProfile

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TrustpilotRetailer:
    domain: str
    profile_url: str
    fallback_score: float
    fallback_reviews: int


@dataclass(frozen=True)
class TrustpilotSnapshot:
    retailer: str
    score: float
    review_count: int
    profile_url: str
    updated_at: Optional[datetime] = None


@dataclass(frozen=True)
class TrustpilotScrapeResult:
    review_counts: dict[str, int]
    errors: dict[str, str]


TrustpilotFetcher = Callable[[], Awaitable[TrustpilotScrapeResult]]


# Fallback används bara innan första lyckade hämtningen eller vid en tom cache.
# Värdena är kontrollerade 2026-07-30.
TRUSTPILOT_RETAILERS: dict[str, TrustpilotRetailer] = {
    "swappie": TrustpilotRetailer(
        "swappie.com",
        "https://se.trustpilot.com/review/swappie.com",
        4.4,
        67_618,
    ),
    "phonehero": TrustpilotRetailer(
        "phonehero.se",
        "https://se.trustpilot.com/review/phonehero.se",
        4.7,
        14_845,
    ),
    "telestore": TrustpilotRetailer(
        "telestore.se",
        "https://se.trustpilot.com/review/telestore.se",
        4.7,
        1_825,
    ),
    "fixmyphone": TrustpilotRetailer(
        "fixmyphone.se",
        "https://se.trustpilot.com/review/fixmyphone.se",
        3.1,
        1_412,
    ),
    "happyphone": TrustpilotRetailer(
        "happyphone.se",
        "https://se.trustpilot.com/review/happyphone.se",
        2.2,
        42,
    ),
    "renewed": TrustpilotRetailer(
        "renewed.se",
        "https://se.trustpilot.com/review/renewed.se",
        4.3,
        43,
    ),
    "fixiphone": TrustpilotRetailer(
        "fixiphone.se",
        "https://se.trustpilot.com/review/fixiphone.se",
        3.9,
        177,
    ),
    "fixphonepro": TrustpilotRetailer(
        "fixtech.se",
        "https://se.trustpilot.com/review/fixtech.se",
        4.0,
        3,
    ),
}


def parse_review_count(value: str) -> int:
    """Tolka Trustpilots synliga heltal, inklusive hårda och smala blanksteg."""
    normalized = re.sub(r"[\s\u00a0\u202f]", "", value)
    if not re.fullmatch(r"\d{1,9}", normalized):
        raise ValueError(f"Ogiltigt antal Trustpilot-omdömen: {value!r}")
    return int(normalized)


async def scrape_trustpilot_review_counts() -> TrustpilotScrapeResult:
    """Läs recensionsantalet från profilhuvudet i en riktig Chromium-session."""
    counts: dict[str, int] = {}
    errors: dict[str, str] = {}
    navigation_timeout_ms = max(60, settings.request_timeout_seconds * 2) * 1000

    async with async_playwright() as playwright:
        launch_options = {
            "headless": settings.playwright_headless,
            "args": ["--no-sandbox", "--disable-dev-shm-usage"],
        }
        if settings.playwright_executable_path.strip():
            launch_options["executable_path"] = settings.playwright_executable_path.strip()

        browser = await playwright.chromium.launch(**launch_options)
        context = await browser.new_context(
            locale="sv-SE",
            timezone_id="Europe/Stockholm",
        )
        page = await context.new_page()

        try:
            for retailer, config in TRUSTPILOT_RETAILERS.items():
                try:
                    try:
                        await page.goto(
                            config.profile_url,
                            wait_until="domcontentloaded",
                            timeout=navigation_timeout_ms,
                        )
                    except PlaywrightTimeoutError:
                        # Kontrollsidan kan fortsätta ladda efter navigationens timeout.
                        pass

                    title = page.locator("h1").filter(has_text="Omdömen")
                    await title.wait_for(state="visible", timeout=navigation_timeout_ms)
                    review_count_text = await title.evaluate(
                        "element => element.nextElementSibling?.textContent || ''"
                    )
                    counts[retailer] = parse_review_count(review_count_text)
                    logger.info("Trustpilot %s: %s omdömen", retailer, counts[retailer])
                except (PlaywrightError, ValueError) as exc:
                    errors[retailer] = str(exc)
                    logger.warning(
                        "Trustpilot-sidan kunde inte läsas för %s: %s",
                        retailer,
                        exc,
                    )
        finally:
            await context.close()
            await browser.close()

    return TrustpilotScrapeResult(review_counts=counts, errors=errors)


def fallback_snapshot(retailer: str) -> Optional[TrustpilotSnapshot]:
    config = TRUSTPILOT_RETAILERS.get(retailer)
    if config is None:
        return None
    return TrustpilotSnapshot(
        retailer=retailer,
        score=config.fallback_score,
        review_count=config.fallback_reviews,
        profile_url=config.profile_url,
    )


async def get_trustpilot_snapshots(
    db: AsyncSession,
    retailers: Iterable[str],
) -> dict[str, TrustpilotSnapshot]:
    """Läs cachevärden och fyll luckor med senast verifierade fallback."""
    requested = list(dict.fromkeys(retailers))
    snapshots = {
        retailer: fallback
        for retailer in requested
        if (fallback := fallback_snapshot(retailer)) is not None
    }
    if not requested:
        return snapshots

    result = await db.execute(
        select(TrustpilotProfile).where(TrustpilotProfile.retailer.in_(requested))
    )
    for profile in result.scalars().all():
        # Gör läsningen tolerant mot test-/proxyresultat som inte är profilrader.
        if not isinstance(profile, TrustpilotProfile):
            continue
        snapshots[profile.retailer] = TrustpilotSnapshot(
            retailer=profile.retailer,
            score=profile.score,
            review_count=profile.review_count,
            profile_url=profile.profile_url,
            updated_at=profile.updated_at,
        )
    return snapshots


async def refresh_trustpilot_profiles(
    db: AsyncSession,
    *,
    fetcher: Optional[TrustpilotFetcher] = None,
) -> dict[str, str]:
    """Scrapa profilerna och uppdatera varje lyckat recensionsantal i cachen."""
    try:
        scrape = await (fetcher or scrape_trustpilot_review_counts)()
    except PlaywrightError as exc:
        logger.exception("Trustpilot-webbläsaren kunde inte starta: %s", exc)
        return {retailer: "error" for retailer in TRUSTPILOT_RETAILERS}

    existing_result = await db.execute(select(TrustpilotProfile))
    existing = {profile.retailer: profile for profile in existing_result.scalars().all()}
    now = datetime.utcnow()
    statuses: dict[str, str] = {}

    for retailer, config in TRUSTPILOT_RETAILERS.items():
        review_count = scrape.review_counts.get(retailer)
        if review_count is None:
            statuses[retailer] = "error"
            continue

        profile = existing.get(retailer)
        if profile is None:
            profile = TrustpilotProfile(
                retailer=retailer,
                score=config.fallback_score,
            )
            db.add(profile)
            existing[retailer] = profile

        profile.domain = config.domain
        profile.profile_url = config.profile_url
        profile.review_count = review_count
        profile.updated_at = now
        statuses[retailer] = "updated"

    await db.commit()
    return statuses
