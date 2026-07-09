import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from .config import settings

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


def setup_scheduler():
    """Konfigurera och starta APScheduler."""
    from .scrapers import run_all_scrapers
    from .database import AsyncSessionLocal
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
        misfire_grace_time=900,
    )

    if settings.used_phone_catalog_update_on_startup:
        scheduler.add_job(
            scheduled_used_phone_catalog,
            trigger=DateTrigger(
                run_date=datetime.now() + timedelta(seconds=20),
                timezone=settings.scrape_timezone,
            ),
            id="used_phone_catalog_startup_refresh",
            name="Uppdatera begagnat-katalog efter startup",
            replace_existing=True,
            max_instances=1,
            misfire_grace_time=300,
        )

    scheduler.start()
    logger.info(
        "✅ Scheduler igång – säljpriser %s:00, begagnat-katalog %s:00 (%s)",
        settings.scrape_cron_hours,
        settings.used_phone_catalog_cron_hours,
        settings.scrape_timezone,
    )
