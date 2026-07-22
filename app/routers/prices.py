import asyncio
import logging

from fastapi import APIRouter, Depends, Query, HTTPException, Header, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import UTC, datetime
from typing import Optional, List, Dict
from pydantic import BaseModel
from ..database import get_db
from ..models import (
    BuybackPrice,
    BuybackPriceHistory,
    PriceSnapshot,
    PriceOut,
    BestOffer,
    ScrapeStatusOut,
)
from ..pricing.crosswalk import FormAnswers, all_conditions, phonehero_conditions
from ..pricing.history import replace_current_buyback_prices
from ..config import settings

router = APIRouter(prefix="/api", tags=["prices"])
logger = logging.getLogger(__name__)


async def _refresh_official_quote(
    quote: "RetailerQuote",
    model: str,
    storage_gb: int,
) -> Optional["RetailerQuote"]:
    """Verifiera publika livepriser och dölj bud som inte kan bekräftas."""
    retailer = quote.retailer.lower()
    if retailer not in {"telestore", "happyphone", "fixmyphone", "renewed"}:
        return quote
    if retailer != "renewed" and not quote.url:
        return None
    try:
        if retailer == "telestore":
            from ..scrapers.telestore import TelestoreScraper

            live_call = TelestoreScraper().fetch_live_quote(
                quote.url,
                storage_gb,
                quote.condition_key,
            )
        elif retailer == "happyphone":
            from ..scrapers.happyphone import HappyPhoneScraper

            live_call = HappyPhoneScraper().fetch_live_quote(
                quote.url,
                storage_gb,
                quote.condition_key,
            )
        elif retailer == "fixmyphone":
            from ..scrapers.fixmyphone import FixMyPhoneScraper

            live_call = FixMyPhoneScraper().fetch_live_quote(
                quote.url,
                storage_gb,
                quote.condition_key,
            )
        else:
            from ..scrapers.renewed import RenewedScraper

            live_call = RenewedScraper().fetch_live_quote(
                model,
                storage_gb,
                quote.condition_key,
            )

        live = await asyncio.wait_for(
            live_call,
            timeout=8,
        )
        if live and int(live["price_sek"]) > 0:
            return RetailerQuote(
                retailer=quote.retailer,
                condition_key=quote.condition_key,
                price_sek=int(live["price_sek"]),
                url=quote.url,
                scraped_at=datetime.now(UTC).replace(tzinfo=None),
            )
    except Exception as exc:
        logger.warning("%s live-verifiering misslyckades: %s", retailer, exc)
    return None


def _normalize_iphone_model(model: str) -> str:
    normalized = " ".join((model or "").strip().split())
    if normalized and not normalized.lower().startswith("iphone"):
        normalized = f"iPhone {normalized}"
    return normalized


def _phonehero_ignores_battery(model: str) -> bool:
    normalized = _normalize_iphone_model(model)
    if normalized.lower() == "iphone air":
        return True
    parts = normalized.split()
    if len(parts) < 2 or parts[0].lower() != "iphone":
        return False
    try:
        generation = int(parts[1])
    except ValueError:
        return False
    return generation >= 16


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


@router.get("/models/storage-options", response_model=Dict[str, List[int]], summary="Lista lagringsalternativ per modell")
async def get_model_storage_options(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(BuybackPrice.model, BuybackPrice.storage_gb)
        .where(BuybackPrice.is_active == True, BuybackPrice.storage_gb.is_not(None))
        .distinct()
        .order_by(BuybackPrice.model, BuybackPrice.storage_gb)
    )

    options: Dict[str, List[int]] = {}
    for model, storage_gb in result.all():
        options.setdefault(model, []).append(storage_gb)

    return options


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
    battery_health_percent: Optional[int] = None
    screen_surface:   str          # LIKE_NEW | ALMOST_NEW | GOOD | MODERATE
    sides_surface:    str
    back_surface:     str
    is_broken:        bool = False
    is_power_broken: bool = False
    is_network_broken: bool = False
    is_face_id_broken: bool = False
    is_selfie_camera_broken: bool = False
    is_speaker_broken: bool = False
    is_charging_or_buttons_broken: bool = False
    is_other_broken: bool = False
    is_screen_broken: bool = False
    is_glass_broken:  bool = False
    is_glass_chipped: bool = False
    is_glass_scratched: bool = False
    is_frame_broken:  bool = False
    is_sides_cracked: bool = False
    is_back_cracked: bool = False
    is_back_camera_broken: bool = False
    is_battery_low:   bool = False
    is_water_damaged: bool = False


class RetailerQuote(BaseModel):
    retailer:      str
    condition_key: str
    price_sek:     int
    url:           Optional[str]
    scraped_at:    datetime


class QuoteResponse(BaseModel):
    model:      str
    storage_gb: int
    quotes:     List[RetailerQuote]
    best_price: Optional[int]
    best_retailer: Optional[str]
    prices_updated_at: Optional[datetime]


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
    model_normalized = _normalize_iphone_model(req.model)

    # 2. Bygg FormAnswers och slå upp condition-nycklar
    answers = FormAnswers(
        screen_surface=req.screen_surface.upper(),
        sides_surface=req.sides_surface.upper(),
        back_surface=req.back_surface.upper(),
        battery_health_percent=req.battery_health_percent,
        is_broken=req.is_broken,
        is_power_broken=req.is_power_broken,
        is_network_broken=req.is_network_broken,
        is_face_id_broken=req.is_face_id_broken,
        is_selfie_camera_broken=req.is_selfie_camera_broken,
        is_speaker_broken=req.is_speaker_broken,
        is_charging_or_buttons_broken=req.is_charging_or_buttons_broken,
        is_other_broken=req.is_other_broken,
        is_screen_broken=req.is_screen_broken,
        is_glass_broken=req.is_glass_broken,
        is_glass_chipped=req.is_glass_chipped,
        is_glass_scratched=req.is_glass_scratched,
        is_frame_broken=req.is_frame_broken,
        is_sides_cracked=req.is_sides_cracked,
        is_back_cracked=req.is_back_cracked,
        is_back_camera_broken=req.is_back_camera_broken,
        is_battery_low=req.is_battery_low,
        is_water_damaged=req.is_water_damaged,
    )
    conditions = all_conditions(answers)  # {retailer: condition_key | None}
    if _phonehero_ignores_battery(model_normalized):
        conditions["phonehero"] = phonehero_conditions(
            answers, model=model_normalized, ignore_battery=True
        )
    else:
        conditions["phonehero"] = phonehero_conditions(answers, model=model_normalized)

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
                BuybackPrice.price_sek > 0,
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
            prices_updated_at=None,
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
            scraped_at=row.scraped_at,
        ))

    # Återförsäljare kan ändra pris mellan de schemalagda fullscraperna.
    # Kontrollera de källor som har ett stabilt publikt live-API/data-calc
    # direkt innan budet visas.
    refreshed_quotes = await asyncio.gather(*(
        _refresh_official_quote(quote, model_normalized, req.storage_gb)
        for quote in quotes
    ))
    quotes = [quote for quote in refreshed_quotes if quote is not None]

    # Sortera fallande på pris
    quotes.sort(key=lambda q: q.price_sek, reverse=True)

    best = quotes[0] if quotes else None
    prices_updated_at = max((q.scraped_at for q in quotes), default=None)
    return QuoteResponse(
        model=model_normalized,
        storage_gb=req.storage_gb,
        quotes=quotes,
        best_price=best.price_sek if best else None,
        best_retailer=best.retailer if best else None,
        prices_updated_at=prices_updated_at,
    )


class ImportPrice(BaseModel):
    model: str
    storage_gb: Optional[int] = None
    condition: Optional[str] = None
    price_sek: int
    url: Optional[str] = None


class PriceSnapshotOut(BaseModel):
    id: int
    market_side: str
    source: str
    retailer: str
    captured_at: datetime
    row_count: int
    added_count: int
    changed_count: int
    removed_count: int
    unchanged_count: int


class PriceHistoryOut(BaseModel):
    retailer: str
    model: str
    storage_gb: Optional[int]
    condition: Optional[str]
    price_sek: int
    currency: str
    valid_from: datetime
    valid_to: Optional[datetime]


def _require_scrape_api_key(x_api_key: str) -> None:
    if x_api_key != settings.scrape_api_key:
        raise HTTPException(status_code=401, detail="Ogiltig API-nyckel")


@router.get(
    "/prices/history/snapshots",
    response_model=List[PriceSnapshotOut],
    summary="Lista historiska pris-snapshots",
)
async def get_price_history_snapshots(
    x_api_key: str = Header(..., alias="X-API-Key"),
    retailer: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    _require_scrape_api_key(x_api_key)
    filters = [PriceSnapshot.market_side == "sell"]
    if retailer:
        filters.append(func.lower(PriceSnapshot.retailer) == retailer.lower())
    result = await db.execute(
        select(PriceSnapshot)
        .where(*filters)
        .order_by(PriceSnapshot.captured_at.desc(), PriceSnapshot.id.desc())
        .limit(limit)
    )
    return [
        PriceSnapshotOut.model_validate(row, from_attributes=True)
        for row in result.scalars().all()
    ]


@router.get(
    "/prices/history",
    response_model=List[PriceHistoryOut],
    summary="Hämta historiska prisperioder",
)
async def get_price_history(
    x_api_key: str = Header(..., alias="X-API-Key"),
    retailer: Optional[str] = Query(None),
    model: Optional[str] = Query(None),
    storage_gb: Optional[int] = Query(None),
    condition: Optional[str] = Query(None),
    active_only: bool = Query(False),
    limit: int = Query(500, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
):
    _require_scrape_api_key(x_api_key)
    if not retailer and not model:
        raise HTTPException(status_code=400, detail="Ange retailer eller model för historikfrågan")

    filters = []
    if retailer:
        filters.append(func.lower(BuybackPriceHistory.retailer) == retailer.lower())
    if model:
        filters.append(func.lower(BuybackPriceHistory.model) == _normalize_iphone_model(model).lower())
    if storage_gb is not None:
        filters.append(BuybackPriceHistory.storage_gb == storage_gb)
    if condition:
        filters.append(func.lower(BuybackPriceHistory.condition) == condition.lower())
    if active_only:
        filters.append(BuybackPriceHistory.valid_to.is_(None))

    result = await db.execute(
        select(BuybackPriceHistory)
        .where(*filters)
        .order_by(
            BuybackPriceHistory.valid_from.desc(),
            BuybackPriceHistory.retailer,
            BuybackPriceHistory.model,
        )
        .limit(limit)
    )
    return [
        PriceHistoryOut.model_validate(row, from_attributes=True)
        for row in result.scalars().all()
    ]


@router.post("/import-prices/{retailer}", summary="Importera förhandshämtade priser (för lokala scrapers)")
async def import_prices(
    retailer: str,
    prices: List[ImportPrice],
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
):
    """
    Tar emot en lista priser från en lokal scraper och sparar dem i DB.
    Arkiverar observationen och ersätter sedan återförsäljarens aktuella prislista.
    Skyddat av API-nyckel.
    """
    _require_scrape_api_key(x_api_key)
    if not prices:
        raise HTTPException(status_code=400, detail="Inga giltiga priser att importera")

    payload = [price.model_dump() for price in prices]
    from ..scrapers import SCRAPERS
    scraper_class = SCRAPERS.get(retailer.lower())
    if scraper_class is not None:
        try:
            payload = await scraper_class().validate_prices(payload, db)
        except RuntimeError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    now = datetime.utcnow()
    snapshot = await replace_current_buyback_prices(
        db,
        retailer=retailer,
        prices=payload,
        captured_at=now,
        source="import",
    )

    await db.commit()
    return {
        "retailer": retailer,
        "imported": len(prices),
        "status": "ok",
        "snapshot_id": snapshot.snapshot_id,
        "history": {
            "added": snapshot.added,
            "changed": snapshot.changed,
            "removed": snapshot.removed,
            "unchanged": snapshot.unchanged,
        },
    }


@router.post("/scrape", summary="Trigga manuell scraping (körs i bakgrunden)")
async def trigger_scrape(
    background_tasks: BackgroundTasks,
    retailer: Optional[str] = Query(None, description="Scrapa bara en specifik återförsäljare"),
    sync: bool = Query(False, description="Kör scrapingen direkt och returnera resultatet"),
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
):
    if x_api_key != settings.scrape_api_key:
        raise HTTPException(status_code=401, detail="Ogiltig API-nyckel")

    from ..scrapers import run_all_scrapers, run_scraper
    from ..database import AsyncSessionLocal
    import logging
    _log = logging.getLogger(__name__)

    if sync:
        try:
            if retailer:
                results = [await run_scraper(retailer, db)]
            else:
                results = await run_all_scrapers(db)
            return {
                "status": "completed",
                "results": [r.model_dump() for r in results],
            }
        except Exception as e:
            _log.exception("[sync-scrape] fel")
            await db.rollback()
            return {
                "status": "error",
                "message": str(e),
                "error_type": type(e).__name__,
            }

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
