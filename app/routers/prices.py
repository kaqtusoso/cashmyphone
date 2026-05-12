from fastapi import APIRouter, Depends, Query, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional, List
from ..database import get_db
from ..models import BuybackPrice, PriceOut, BestOffer, ScrapeStatusOut
from ..config import settings

router = APIRouter(prefix="/api", tags=["prices"])


def _active_prices(model=None, storage_gb=None, condition=None, retailer=None):
    """Bygg ett filtrerat query för aktiva priser."""
    filters = [BuybackPrice.is_active == True]
    if model:
        filters.append(func.lower(BuybackPrice.model).contains(model.lower()))
    if storage_gb:
        filters.append(BuybackPrice.storage_gb == storage_gb)
    if condition:
        filters.append(func.lower(BuybackPrice.condition) == condition.lower())
    if retailer:
        filters.append(func.lower(BuybackPrice.retailer) == retailer.lower())
    return and_(*filters)


@router.get("/prices", response_model=List[PriceOut], summary="Hämta alla priser")
async def get_prices(
    model: Optional[str] = Query(None, description='Filtrera på modell, t.ex. "iPhone 15 Pro"'),
    storage_gb: Optional[int] = Query(None, description="Filtrera på lagring i GB"),
    condition: Optional[str] = Query(None, description='Skick: "utmärkt", "bra", "okej"'),
    retailer: Optional[str] = Query(None, description="Filtrera på återförsäljare"),
    limit: int = Query(200, le=500),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BuybackPrice)
        .where(_active_prices(model, storage_gb, condition, retailer))
        .order_by(BuybackPrice.model, BuybackPrice.storage_gb, BuybackPrice.price_sek.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/prices/best", response_model=List[BestOffer], summary="Bästa bud per modell/lagring/skick")
async def get_best_offers(
    model: Optional[str] = Query(None),
    storage_gb: Optional[int] = Query(None),
    condition: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    # Hämta alla matchande priser
    result = await db.execute(
        select(BuybackPrice)
        .where(_active_prices(model, storage_gb, condition))
        .order_by(BuybackPrice.model, BuybackPrice.storage_gb, BuybackPrice.condition, BuybackPrice.price_sek.desc())
    )
    rows = result.scalars().all()

    # Gruppera per (model, storage_gb, condition)
    groups: dict = {}
    for row in rows:
        key = (row.model, row.storage_gb, row.condition)
        if key not in groups:
            groups[key] = []
        groups[key].append(row)

    offers = []
    for (m, s, c), prices in groups.items():
        best = prices[0]  # Redan sorterat fallande på pris
        offers.append(BestOffer(
            model=m,
            storage_gb=s,
            condition=c,
            best_retailer=best.retailer,
            best_price_sek=best.price_sek,
            all_offers=[PriceOut.model_validate(p) for p in prices],
        ))

    return offers


@router.get("/models", response_model=List[str], summary="Lista tillgängliga modeller")
async def get_models(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(BuybackPrice.model)
        .where(BuybackPrice.is_active == True)
        .distinct()
        .order_by(BuybackPrice.model)
    )
    return [row[0] for row in result.all()]


@router.get("/retailers", response_model=List[str], summary="Lista aktiva återförsäljare")
async def get_retailers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(BuybackPrice.retailer)
        .where(BuybackPrice.is_active == True)
        .distinct()
        .order_by(BuybackPrice.retailer)
    )
    return [row[0] for row in result.all()]


@router.post("/scrape", response_model=List[ScrapeStatusOut], summary="Trigga manuell scraping")
async def trigger_scrape(
    retailer: Optional[str] = Query(None, description="Scrapa bara en specifik återförsäljare"),
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
):
    if x_api_key != settings.scrape_api_key:
        raise HTTPException(status_code=401, detail="Ogiltig API-nyckel")

    from ..scrapers import run_all_scrapers, run_scraper
    if retailer:
        results = [await run_scraper(retailer, db)]
    else:
        results = await run_all_scrapers(db)

    return results
