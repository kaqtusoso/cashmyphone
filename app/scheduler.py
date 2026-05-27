import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from .config import settings

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


def setup_scheduler():
    """Konfigurera och starta APScheduler."""
    from .scrapers import run_all_scrapers
    from .database import AsyncSessionLocal

    async def scheduled_scrape():
        logger.info("⏰ Schemalagd scraping startar...")
        async with AsyncSessionLocal() as db:
            results = await run_all_scrapers(db)
            for r in results:
                logger.info(f"  {r.retailer}: {r.status} – {r.prices_found} priser")

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

    scheduler.start()
    logger.info(
        "✅ Scheduler igång – kör %s:00 (%s)",
        settings.scrape_cron_hours,
        settings.scrape_timezone,
    )
