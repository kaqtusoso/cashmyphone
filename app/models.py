from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Float, Boolean, DateTime, Text, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from pydantic import BaseModel, ConfigDict
from .database import Base


# ─── SQLAlchemy ORM-modell ───────────────────────────────────────────────────

class BuybackPrice(Base):
    """Lagrar inköpspriser för iPhones från varje återförsäljare."""
    __tablename__ = "buyback_prices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    retailer: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    model: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    storage_gb: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    condition: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    price_sek: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="SEK")
    url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (
        Index("ix_retailer_model_storage_condition",
              "retailer", "model", "storage_gb", "condition"),
    )


class ScraperRun(Base):
    """Loggar varje scraping-körning för felsökning och historik."""
    __tablename__ = "scraper_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    retailer: Mapped[str] = mapped_column(String(50), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="running")  # running | success | error
    prices_found: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class PriceSnapshot(Base):
    """En lyckad inläsning av en återförsäljares kompletta prislista."""
    __tablename__ = "price_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    market_side: Mapped[str] = mapped_column(String(20), default="sell", nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    retailer: Mapped[str] = mapped_column(String(50), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False)
    added_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    changed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    removed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unchanged_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    __table_args__ = (
        Index("ix_price_snapshots_retailer_captured_at", "retailer", "captured_at"),
        Index("ix_price_snapshots_market_side_captured_at", "market_side", "captured_at"),
    )


class BuybackPriceHistory(Base):
    """Prisperioder som gör varje historiskt buyback-läge återskapningsbart."""
    __tablename__ = "buyback_price_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_id: Mapped[int] = mapped_column(
        ForeignKey("price_snapshots.id"), nullable=False, index=True
    )
    retailer: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    storage_gb: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    condition: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    price_sek: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="SEK", nullable=False)
    url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    valid_from: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    valid_to: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index(
            "ix_buyback_history_lookup",
            "retailer",
            "model",
            "storage_gb",
            "condition",
            "valid_to",
        ),
        Index("ix_buyback_history_valid_from", "valid_from"),
    )


class TrustpilotProfile(Base):
    """Senast hämtade Trustpilot-data per återförsäljare."""
    __tablename__ = "trustpilot_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    retailer: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    domain: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    profile_url: Mapped[str] = mapped_column(Text, nullable=False, default="")
    business_unit_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    review_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


# ─── Pydantic-scheman (API-svar) ─────────────────────────────────────────────

class PriceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    retailer: str
    model: str
    storage_gb: Optional[int]
    condition: Optional[str]
    price_sek: int
    currency: str
    url: Optional[str]
    scraped_at: datetime


class BestOffer(BaseModel):
    model: str
    storage_gb: Optional[int]
    condition: Optional[str]
    best_retailer: str
    best_price_sek: int
    all_offers: list[PriceOut]


class ScrapeStatusOut(BaseModel):
    retailer: str
    status: str
    message: str
    prices_found: int = 0
