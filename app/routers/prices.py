from fastapi import APIRouter, Depends, Query, HTTPException, Header, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import Optional, List
from pydantic import BaseModel
from ..database import get_db
from ..models import BuybackPrice, PriceOut, BestOffer, ScrapeStatusOut
from ..pricing.crosswalk import FormAnswers, all_conditions
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


# ─── /api/quote ──────────────────────────────────────────────────────────────

class QuoteRequest(BaseModel):
    """Formulärsvar från CashMyPhone — en iPhone utvärderas."""
    model: str
    storage_gb: int
    screen_surface:   str          # LIKE_NEW | ALMOST_NEW | GOOD | MODERATE
    sides_surface:    str
    back_surface:     str
    is_broken:        bool = False
    is_screen_broken: bool = False
    is_glass_broken:  bool = False
    is_battery_low:   bool = False
    is_water_damaged: bool = False


class RetailerQuote(BaseModel):
    retailer:      str
    condition_key: str
    price_sek:     int
    url:           Optional[str]


class QuoteResponse(BaseModel):
    model:      str
    storage_gb: int
    quotes:     List[RetailerQuote]
    best_price: Optional[int]
    best_retailer: Optional[str]


@router.post(
    "/quote",
    response_model=QuoteResponse,
    summary="Hämta bud från alla återförsäljare för ett formulärsvar",
    description=(
        "Tar in formulärsvar (modell, lagring, ytskick, funktionsflaggor) "
        "och returnerar det bästa budet från varje återförsäljare som köper "
        "den kombinationen, sorterat fallande på pris."
    ),
)
async def get_quote(
    req: QuoteRequest,
    db: AsyncSession = Depends(get_db),
):
    # 1. Normalisera modellnamnet (lägg till "iPhone " om det saknas)
    model_normalized = req.model.strip()
    if not model_normalized.lower().startswith("iphone"):
        model_normalized = f"iPhone {model_normalized}"

    # 2. Bygg FormAnswers och slå upp condition-nycklar
    answers = FormAnswers(
        screen_surface=req.screen_surface.upper(),
        sides_surface=req.sides_surface.upper(),
        back_surface=req.back_surface.upper(),
        is_broken=req.is_broken,
        is_screen_broken=req.is_screen_broken,
        is_glass_broken=req.is_glass_broken,
        is_battery_low=req.is_battery_low,
        is_water_damaged=req.is_water_damaged,
    )
    conditions = all_conditions(answers)  # {retailer: condition_key | None}

    # 3. Hämta det bästa (högsta) priset per återförsäljare i ett enda DB-anrop
    #    Bygg OR-filter: (retailer='swappie' AND condition='…') OR …
    retailer_filters = []
    active_retailers: List[str] = []  # de som faktiskt lägger bud
    for retailer, ckey in conditions.items():
        if ckey is None:
            continue  # t.ex. Telestore om enheten inte fungerar
        active_retailers.append(retailer)
        condition_keys = ckey if isinstance(ckey, list) else [ckey]
        retailer_filters.append(
            and_(
                func.lower(BuybackPrice.retailer)  == retailer,
                func.lower(BuybackPrice.condition).in_([c.lower() for c in condition_keys]),
                func.lower(BuybackPrice.model) == model_normalized.lower(),
                BuybackPrice.storage_gb == req.storage_gb,
                BuybackPrice.is_active == True,
            )
        )

    if not retailer_filters:
        # Ingen återförsäljare lägger bud (t.ex. enheten fungerar inte)
        return QuoteResponse(
            model=model_normalized,
            storage_gb=req.storage_gb,
            quotes=[],
            best_price=None,
            best_retailer=None,
        )

    result = await db.execute(
        select(BuybackPrice)
        .where(or_(*retailer_filters))
        .order_by(BuybackPrice.retailer, BuybackPrice.price_sek.desc())
    )
    rows = result.scalars().all()

    # 4. Plocka bästa priset per återförsäljare (första i fallande ordning)
    seen: set = set()
    quotes: List[RetailerQuote] = []
    for row in rows:
        if row.retailer in seen:
            continue
        seen.add(row.retailer)
        quotes.append(RetailerQuote(
            retailer=row.retailer,
            condition_key=row.condition,
            price_sek=row.price_sek,
            url=row.url,
        ))

    # Sortera fallande på pris
    quotes.sort(key=lambda q: q.price_sek, reverse=True)

    best = quotes[0] if quotes else None
    return QuoteResponse(
        model=model_normalized,
        storage_gb=req.storage_gb,
        quotes=quotes,
        best_price=best.price_sek if best else None,
        best_retailer=best.retailer if best else None,
    )


class ImportPrice(BaseModel):
    model: str
    storage_gb: Optional[int] = None
    condition: Optional[str] = None
    price_sek: int
    url: Optional[str] = None


@router.post("/import-prices/{retailer}", summary="Importera förhandshämtade priser (för lokala scrapers)")
async def import_prices(
    retailer: str,
    prices: List[ImportPrice],
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
):
    """
    Tar emot en lista priser från en lokal scraper och sparar dem i DB.
    Markerar alla befintliga priser för återförsäljaren som inaktiva först.
    Skyddat av API-nyckel.
    """
    if x_api_key != settings.scrape_api_key:
        raise HTTPException(status_code=401, detail="Ogiltig API-nyckel")

    from sqlalchemy import update
    from datetime import datetime

    # Markera gamla priser som inaktiva
    await db.execute(
        update(BuybackPrice)
        .where(func.lower(BuybackPrice.retailer) == retailer.lower())
        .values(is_active=False)
    )

    # Infoga nya priser
    now = datetime.utcnow()
    for p in prices:
        db.add(BuybackPrice(
            retailer=retailer.lower(),
            model=p.model,
            storage_gb=p.storage_gb,
            condition=p.condition,
            price_sek=p.price_sek,
            url=p.url,
            scraped_at=now,
            is_active=True,
        ))

    await db.commit()
    return {"retailer": retailer, "imported": len(prices), "status": "ok"}


@router.post("/scrape", summary="Trigga manuell scraping (körs i bakgrunden)")
async def trigger_scrape(
    background_tasks: BackgroundTasks,
    retailer: Optional[str] = Query(None, description="Scrapa bara en specifik återförsäljare"),
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
):
    if x_api_key != settings.scrape_api_key:
        raise HTTPException(status_code=401, detail="Ogiltig API-nyckel")

    from ..scrapers import run_all_scrapers, run_scraper
    from ..database import AsyncSessionLocal
    import logging
    _log = logging.getLogger(__name__)

    async def _run_in_background():
        async with AsyncSessionLocal() as session:
            try:
                if retailer:
                    results = [await run_scraper(retailer, session)]
                else:
                    results = await run_all_scrapers(session)
                for r in results:
                    _log.info(f"[bg-scrape] {r.retailer}: {r.status} – {r.message}")
            except Exception as e:
                _log.error(f"[bg-scrape] fel: {e}")

    background_tasks.add_task(_run_in_background)
    return {"status": "started", "message": "Scraping körs i bakgrunden. Kolla deploy-loggarna för resultat."}
