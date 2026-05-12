from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Float, Boolean, DateTime, Text, Index
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
    condition: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
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
