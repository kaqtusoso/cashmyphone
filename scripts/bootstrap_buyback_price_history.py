"""Bevara dagens aktiva buyback-priser som historikens startpunkt."""

import asyncio
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.database import AsyncSessionLocal, init_db
from app.pricing.history import bootstrap_all_current_prices


async def main() -> None:
    await init_db()
    async with AsyncSessionLocal() as db:
        snapshots = await bootstrap_all_current_prices(db)
        await db.commit()

    if not snapshots:
        print("Prishistoriken var redan initierad; inga nya start-snapshots skapades.")
        return

    total_rows = sum(snapshot.rows for snapshot in snapshots)
    print(
        f"Skapade {len(snapshots)} start-snapshots med "
        f"{total_rows} historiska prisrader."
    )


if __name__ == "__main__":
    asyncio.run(main())
