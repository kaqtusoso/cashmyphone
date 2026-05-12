import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
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
        trigger=IntervalTrigger(hours=settings.scrape_interval_hours),
        id="scrape_all",
        name="Scrapa alla återförsäljare",
        replace_existing=True,
        misfire_grace_time=300,
    )

    scheduler.start()
    logger.info(f"✅ Scheduler igång – kör var {settings.scrape_interval_hours}:e timme")
