import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .database import init_db
from .scheduler import setup_scheduler, scheduler
from .routers import orders, prices
from .config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
DIST_DIR = Path(__file__).resolve().parent.parent / "dist"
INDEX_HTML = DIST_DIR / "index.html"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 CashMyPhone API startar...")
    await init_db()
    setup_scheduler()
    yield
    # Shutdown
    scheduler.shutdown(wait=False)
    logger.info("👋 CashMyPhone API avslutar")


app = FastAPI(
    title="CashMyPhone API",
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


@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/", tags=["system"])
async def root():
    if INDEX_HTML.exists():
        return FileResponse(INDEX_HTML)

    return {
        "name": "CashMyPhone API",
        "docs": "/docs",
        "endpoints": [
            "/api/prices",
            "/api/prices/best",
            "/api/models",
            "/api/retailers",
            "/api/quote",
            "/api/orders",
            "/api/scrape",
            "/api/import-prices/{retailer}",
        ],
    }


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
