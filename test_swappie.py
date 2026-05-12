"""
Lokal test: kör Swappie-scrapern och visa resultatet.
Kör: python test_swappie.py
"""
import asyncio
import sys
import os
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:////tmp/test.db")

from app.scrapers.swappie import SwappieScraper

async def main():
    model_filter = sys.argv[1] if len(sys.argv) > 1 else None
    scraper = SwappieScraper()

    print(f"Kör Swappie-scraper{f' för {model_filter}' if model_filter else ' (alla modeller)'}...")
    prices = await scraper.fetch_prices()

    if model_filter:
        prices = [p for p in prices if model_filter.lower() in p["model"].lower()]

    if not prices:
        print("Inga priser hittades.")
        return

    # Gruppera per modell
    from collections import defaultdict
    by_model = defaultdict(list)
    for p in prices:
        by_model[p["model"]].append(p)

    print(f"\n{'='*55}")
    print(f"  Totalt: {len(prices)} priser för {len(by_model)} modeller")
    print(f"{'='*55}")

    CONDITION_ORDER = ["sealed_box", "like_new", "almost_new", "good", "moderate"]
    CONDITION_LABELS = {
        "sealed_box":  "Förseglad låda",
        "like_new":    "Som ny",
        "almost_new":  "Nästan ny",
        "good":        "Bra skick",
        "moderate":    "Godkänt skick",
    }

    for model in sorted(by_model.keys()):
        model_prices = by_model[model]
        storages = sorted(set(p["storage_gb"] for p in model_prices if p["storage_gb"]))
        print(f"\n{model}")
        header = f"  {'Skick':<18}" + "".join(f"{s}GB".rjust(9) for s in storages)
        print(header)
        print("  " + "-" * (16 + 9 * len(storages)))
        for cond in CONDITION_ORDER:
            row_prices = {
                p["storage_gb"]: p["price_sek"]
                for p in model_prices if p["condition"] == cond
            }
            if not row_prices:
                continue
            label = CONDITION_LABELS.get(cond, cond)
            row = f"  {label:<18}" + "".join(
                f"{row_prices.get(s, '-'):>8} " for s in storages
            )
            print(row)

if __name__ == "__main__":
    asyncio.run(main())
