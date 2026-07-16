"""Central, kompakt historik för Televeras buyback-priser.

Varje lyckad inläsning loggas i ``price_snapshots``. Själva prisraderna
lagras som giltighetsperioder och får därför bara en ny rad när ett pris
tillkommer eller ändras. Det aktuella offert-API:t fortsätter att läsa den
separata tabellen ``buyback_prices``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from typing import Any, Iterable, Mapping, Sequence

from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import BuybackPrice, BuybackPriceHistory, PriceSnapshot


PriceKey = tuple[str, int | None, str | None]


@dataclass(frozen=True)
class SnapshotStats:
    snapshot_id: int
    rows: int
    added: int
    changed: int
    removed: int
    unchanged: int


def _canonical_prices(prices: Iterable[Mapping[str, Any]]) -> dict[PriceKey, dict[str, Any]]:
    canonical: dict[PriceKey, dict[str, Any]] = {}
    for raw in prices:
        model = str(raw["model"]).strip()
        storage_gb = raw.get("storage_gb")
        condition = raw.get("condition")
        key = (model, storage_gb, condition)
        row = {
            "model": model,
            "storage_gb": storage_gb,
            "condition": condition,
            "price_sek": int(raw["price_sek"]),
            "currency": str(raw.get("currency") or "SEK"),
            "url": raw.get("url"),
        }
        previous = canonical.get(key)
        if previous and (
            previous["price_sek"] != row["price_sek"]
            or previous["currency"] != row["currency"]
        ):
            raise ValueError(f"Motstridiga priser för samma nyckel: {key}")
        canonical[key] = row
    return canonical


def _content_hash(rows: Mapping[PriceKey, Mapping[str, Any]]) -> str:
    payload = [
        [model, storage_gb, condition, row["price_sek"], row["currency"]]
        for (model, storage_gb, condition), row in rows.items()
    ]
    payload.sort(key=lambda row: (row[0], row[1] if row[1] is not None else -1, row[2] or ""))
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


async def _close_history_rows(
    db: AsyncSession,
    row_ids: Sequence[int],
    valid_to: datetime,
) -> None:
    # SQLite har en låg gräns för antal bundna parametrar i en fråga.
    for offset in range(0, len(row_ids), 500):
        chunk = row_ids[offset : offset + 500]
        await db.execute(
            update(BuybackPriceHistory)
            .where(BuybackPriceHistory.id.in_(chunk))
            .values(valid_to=valid_to)
        )


async def record_buyback_snapshot(
    db: AsyncSession,
    *,
    retailer: str,
    prices: Iterable[Mapping[str, Any]],
    captured_at: datetime,
    source: str,
) -> SnapshotStats:
    """Spara en komplett observation och komprimera oförändrade prisperioder."""
    retailer = retailer.lower()
    incoming = _canonical_prices(prices)
    digest = _content_hash(incoming)

    latest = (
        await db.execute(
            select(PriceSnapshot)
            .where(
                PriceSnapshot.market_side == "sell",
                PriceSnapshot.retailer == retailer,
            )
            .order_by(PriceSnapshot.captured_at.desc(), PriceSnapshot.id.desc())
            .limit(1)
            .with_for_update()
        )
    ).scalar_one_or_none()

    if latest and latest.content_hash == digest:
        snapshot = PriceSnapshot(
            market_side="sell",
            source=source,
            retailer=retailer,
            captured_at=captured_at,
            row_count=len(incoming),
            added_count=0,
            changed_count=0,
            removed_count=0,
            unchanged_count=len(incoming),
            content_hash=digest,
        )
        db.add(snapshot)
        await db.flush()
        return SnapshotStats(snapshot.id, len(incoming), 0, 0, 0, len(incoming))

    active_result = await db.execute(
        select(
            BuybackPriceHistory.id,
            BuybackPriceHistory.model,
            BuybackPriceHistory.storage_gb,
            BuybackPriceHistory.condition,
            BuybackPriceHistory.price_sek,
            BuybackPriceHistory.currency,
        )
        .where(
            BuybackPriceHistory.retailer == retailer,
            BuybackPriceHistory.valid_to.is_(None),
        )
        .with_for_update()
    )
    active = {
        (row.model, row.storage_gb, row.condition): row
        for row in active_result.all()
    }

    added_keys = incoming.keys() - active.keys()
    removed_keys = active.keys() - incoming.keys()
    shared_keys = incoming.keys() & active.keys()
    changed_keys = {
        key
        for key in shared_keys
        if incoming[key]["price_sek"] != active[key].price_sek
        or incoming[key]["currency"] != active[key].currency
    }
    unchanged_count = len(shared_keys) - len(changed_keys)

    snapshot = PriceSnapshot(
        market_side="sell",
        source=source,
        retailer=retailer,
        captured_at=captured_at,
        row_count=len(incoming),
        added_count=len(added_keys),
        changed_count=len(changed_keys),
        removed_count=len(removed_keys),
        unchanged_count=unchanged_count,
        content_hash=digest,
    )
    db.add(snapshot)
    await db.flush()

    rows_to_close = [active[key].id for key in removed_keys | changed_keys]
    await _close_history_rows(db, rows_to_close, captured_at)

    rows_to_open = added_keys | changed_keys
    if rows_to_open:
        await db.execute(
            insert(BuybackPriceHistory),
            [
                {
                    "snapshot_id": snapshot.id,
                    "retailer": retailer,
                    **incoming[key],
                    "valid_from": captured_at,
                    "valid_to": None,
                }
                for key in rows_to_open
            ],
        )

    return SnapshotStats(
        snapshot.id,
        len(incoming),
        len(added_keys),
        len(changed_keys),
        len(removed_keys),
        unchanged_count,
    )


def _current_row_to_dict(row: BuybackPrice) -> dict[str, Any]:
    return {
        "model": row.model,
        "storage_gb": row.storage_gb,
        "condition": row.condition,
        "price_sek": row.price_sek,
        "currency": row.currency,
        "url": row.url,
    }


async def ensure_retailer_history_seeded(
    db: AsyncSession,
    retailer: str,
) -> SnapshotStats | None:
    """Bevara den befintliga latest-only-listan innan första historiska importen."""
    retailer = retailer.lower()
    snapshot_exists = await db.scalar(
        select(func.count(PriceSnapshot.id)).where(
            PriceSnapshot.market_side == "sell",
            PriceSnapshot.retailer == retailer,
        )
    )
    if snapshot_exists:
        return None

    current = (
        await db.execute(
            select(BuybackPrice).where(
                func.lower(BuybackPrice.retailer) == retailer,
                BuybackPrice.is_active.is_(True),
            )
        )
    ).scalars().all()
    if not current:
        return None

    captured_at = max(row.scraped_at for row in current)
    return await record_buyback_snapshot(
        db,
        retailer=retailer,
        prices=(_current_row_to_dict(row) for row in current),
        captured_at=captured_at,
        source="bootstrap",
    )


async def replace_current_buyback_prices(
    db: AsyncSession,
    *,
    retailer: str,
    prices: Iterable[Mapping[str, Any]],
    captured_at: datetime,
    source: str,
) -> SnapshotStats:
    """Arkivera en komplett lista och ersätt därefter live-tabellen atomärt."""
    retailer = retailer.lower()
    incoming = _canonical_prices(prices)

    await ensure_retailer_history_seeded(db, retailer)
    stats = await record_buyback_snapshot(
        db,
        retailer=retailer,
        prices=incoming.values(),
        captured_at=captured_at,
        source=source,
    )

    await db.execute(
        delete(BuybackPrice).where(func.lower(BuybackPrice.retailer) == retailer)
    )
    if incoming:
        await db.execute(
            insert(BuybackPrice),
            [
                {
                    "retailer": retailer,
                    **row,
                    "scraped_at": captured_at,
                    "is_active": True,
                }
                for row in incoming.values()
            ],
        )
    return stats


async def bootstrap_all_current_prices(
    db: AsyncSession,
    *,
    commit_each: bool = False,
) -> list[SnapshotStats]:
    """Skapa startpunkter för alla prislistor i en befintlig latest-only-databas."""
    retailer_rows = (
        await db.execute(
            select(BuybackPrice.retailer, func.count(BuybackPrice.id))
            .where(BuybackPrice.is_active.is_(True))
            .group_by(BuybackPrice.retailer)
            .order_by(func.count(BuybackPrice.id), BuybackPrice.retailer)
        )
    ).all()
    results: list[SnapshotStats] = []
    for retailer, _row_count in retailer_rows:
        stats = await ensure_retailer_history_seeded(db, retailer)
        if stats:
            results.append(stats)
            if commit_each:
                await db.commit()
    return results
