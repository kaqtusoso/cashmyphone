import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from sqlalchemy import func, select
from .config import settings

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()

USED_PHONE_CATALOG_STARTUP_DELAY_SECONDS = 20
USED_PHONE_CATALOG_MISFIRE_GRACE_SECONDS = 12 * 60 * 60


def _used_phone_catalog_startup_run_date(now: datetime | None = None) -> datetime:
    """Return an aware instant so host timezone cannot shift the startup job."""
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise ValueError("Startup run date requires a timezone-aware datetime")
    return current + timedelta(seconds=USED_PHONE_CATALOG_STARTUP_DELAY_SECONDS)


async def scrape_if_prices_empty():
    """Populate the price database once when a fresh SQLite volume is empty."""
    from .database import AsyncSessionLocal
    from .models import BuybackPrice
    from .scrapers import run_all_scrapers

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(func.count()).select_from(BuybackPrice))
        price_count = result.scalar_one()
        if price_count:
            logger.info("✅ Prisdatabasen innehåller redan %s priser; hoppar över startup-scrape", price_count)
            return

        logger.info("📦 Prisdatabasen är tom; kör startup-scrape för att fylla SQLite-volymen")
        results = await run_all_scrapers(db)
        for r in results:
            logger.info("  %s: %s – %s priser", r.retailer, r.status, r.prices_found)


def setup_scheduler():
    """Konfigurera och starta APScheduler."""
    from .scrapers import run_all_scrapers
    from .database import AsyncSessionLocal
    from .routers.orders import run_order_feedback_emails
    from scripts.update_used_phone_catalog import update_used_phone_catalog

    async def scheduled_scrape():
        logger.info("⏰ Schemalagd scraping startar...")
        async with AsyncSessionLocal() as db:
            results = await run_all_scrapers(db)
            for r in results:
                logger.info(f"  {r.retailer}: {r.status} – {r.prices_found} priser")

    async def scheduled_used_phone_catalog():
        logger.info("📱 Schemalagd uppdatering av begagnat-katalog startar...")
        result = await update_used_phone_catalog()
        catalog = result["catalog"]
        scraper_errors = [r for r in result["scrapers"] if r["status"] != "success"]
        logger.info(
            "Begagnat-katalog uppdaterad: %s erbjudanden, %s modeller",
            catalog["offers"],
            catalog["models"],
        )
        if scraper_errors:
            logger.warning(
                "Begagnat-katalogen uppdaterades med %s scraperfel: %s",
                len(scraper_errors),
                ", ".join(f"{r['retailer']}={r.get('error_type')}" for r in scraper_errors),
            )

    async def scheduled_feedback_emails():
        logger.info("📩 Schemalagda feedbackmail startar...")
        result = await run_order_feedback_emails()
        if result.ok:
            logger.info(result.message)
        else:
            logger.warning(result.message)

    scheduler.add_job(
        scheduled_scrape,
        trigger=CronTrigger(
            hour=settings.scrape_cron_hours,
            minute=0,
            timezone=settings.scrape_timezone,
        ),
        id="scrape_all",
        name="Scrapa alla återförsäljare",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=300,
    )

    scheduler.add_job(
        scheduled_used_phone_catalog,
        trigger=CronTrigger(
            hour=settings.used_phone_catalog_cron_hours,
            minute=0,
            timezone=settings.scrape_timezone,
        ),
        id="used_phone_catalog_refresh",
        name="Uppdatera begagnat-katalog",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=USED_PHONE_CATALOG_MISFIRE_GRACE_SECONDS,
    )

    if settings.feedback_email_enabled:
        scheduler.add_job(
            scheduled_feedback_emails,
            trigger=CronTrigger(
                hour=settings.feedback_email_cron_hour,
                minute=settings.feedback_email_cron_minute,
                timezone=settings.scrape_timezone,
            ),
            id="order_feedback_emails",
            name="Skicka Trustpilot-feedbackmail",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=900,
        )

    if settings.used_phone_catalog_update_on_startup:
        scheduler.add_job(
            scheduled_used_phone_catalog,
            trigger=DateTrigger(
                run_date=_used_phone_catalog_startup_run_date(),
                timezone=settings.scrape_timezone,
            ),
            id="used_phone_catalog_startup_refresh",
            name="Uppdatera begagnat-katalog efter startup",
            replace_existing=True,
            max_instances=1,
            misfire_grace_time=USED_PHONE_CATALOG_MISFIRE_GRACE_SECONDS,
        )

    scheduler.start()
    logger.info(
        "✅ Scheduler igång – säljpriser %s:00, begagnat-katalog %s:00, feedbackmail %s (%s)",
        settings.scrape_cron_hours,
        settings.used_phone_catalog_cron_hours,
        (
            f"{settings.feedback_email_cron_hour:02d}:{settings.feedback_email_cron_minute:02d}"
            if settings.feedback_email_enabled
            else "av"
        ),
        settings.scrape_timezone,
    )
