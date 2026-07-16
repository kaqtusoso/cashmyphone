import logging
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .database import AsyncSessionLocal, init_db
from .pricing.history import bootstrap_all_current_prices
from .scheduler import setup_scheduler, scheduler, scrape_if_prices_empty
from .routers import orders, prices, used_phones
from .config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
DIST_DIR = Path(__file__).resolve().parent.parent / "dist"
INDEX_HTML = DIST_DIR / "index.html"
PUBLIC_DIR = Path(__file__).resolve().parent.parent / "public"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Televera API startar...")
    await init_db()
    async with AsyncSessionLocal() as db:
        snapshots = await bootstrap_all_current_prices(db)
        await db.commit()
    if snapshots:
        logger.info(
            "📚 Prishistorik initierad: %s snapshots, %s prisrader",
            len(snapshots),
            sum(snapshot.rows for snapshot in snapshots),
        )
    setup_scheduler()
    asyncio.create_task(scrape_if_prices_empty())
    yield
    # Shutdown
    scheduler.shutdown(wait=False)
    logger.info("👋 Televera API avslutar")


app = FastAPI(
    title="Televera API",
    description="Jämför inköpspriser för begagnade iPhones från svenska återförsäljare",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(prices.router)
app.include_router(orders.router)
app.include_router(used_phones.router)


@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok", "version": "1.0.0", "order_email_template": "televera-2026-07-13-dynamic-shipping-v2"}


@app.get("/", tags=["system"])
async def root():
    if INDEX_HTML.exists():
        return FileResponse(INDEX_HTML)

    return {
        "name": "Televera API",
        "docs": "/docs",
        "endpoints": [
            "/api/prices",
            "/api/prices/best",
            "/api/models",
            "/api/retailers",
            "/api/quote",
            "/api/orders",
            "/api/used-phones",
            "/api/used-phones/models",
            "/api/used-phones/status",
            "/api/scrape",
            "/api/scrape/status",
            "/api/import-prices/{retailer}",
        ],
    }


@app.get("/mail-assets/televera-logo-full.png", include_in_schema=False)
async def televera_email_logo():
    return FileResponse(PUBLIC_DIR / "televera-logo-full.png", media_type="image/png")


if (DIST_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="assets")


@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa(full_path: str):
    requested_file = DIST_DIR / full_path
    if requested_file.is_file():
        return FileResponse(requested_file)
    if INDEX_HTML.exists():
        return FileResponse(INDEX_HTML)
    return {"detail": "Not Found"}
