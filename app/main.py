import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import init_db
from .scheduler import setup_scheduler, scheduler
from .routers import prices
from .config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


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


@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/", tags=["system"])
async def root():
    return {
        "name": "CashMyPhone API",
        "docs": "/docs",
        "endpoints": ["/api/prices", "/api/prices/best", "/api/models", "/api/retailers"],
    }
