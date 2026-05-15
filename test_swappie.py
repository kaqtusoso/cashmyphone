"""
Lokal test: kör Swappie-scrapern och visa hela primatrisen.

Användning:
  python test_swappie.py                   # alla modeller
  python test_swappie.py "iPhone 17"       # filtrera på modell
  python test_swappie.py "iPhone 17" 256   # filtrera på modell + lagring

Condition-nyckelformat:
  LIKE_NEW              → perfekt skick, inga funktionella fel
  LIKE_NEW:BAT          → perfekt skick, batteri under 80%
  GOOD:B,BS             → bra skick, startar ej + trasig skärm
  Koder: B=startar ej, BAT=batteri<80%, BG=krackelerat glas, BS=trasig skärm
"""
import asyncio
import sys
import os
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:////tmp/test.db")

from collections import defaultdict
from app.scrapers.swappie import SwappieScraper, BATTERY_THRESHOLD

VISUAL_ORDER = ["SEALED_BOX", "LIKE_NEW", "ALMOST_NEW", "GOOD", "MODERATE"]
VISUAL_LABELS = {
    "SEALED_BOX":  "Förseglad",
    "LIKE_NEW":    "Som ny",
    "ALMOST_NEW":  "Nästan ny",
    "GOOD":        "Bra skick",
    "MODERATE":    "Godkänt",
}

FUNC_LABELS = {
    "B":   "Startar ej",
    "BAT": f"Batteri <{BATTERY_THRESHOLD}% (battery issue)",
    "BG":  "Krackelerat glas",
    "BS":  "Trasig skärm",
}


def parse_condition(cond: str):
    """'GOOD:B,BS' → ('GOOD', ['B', 'BS'])"""
    if ":" in cond:
        visual, rest = cond.split(":", 1)
        return visual, rest.split(",")
    return cond, []


async def main():
    model_filter = sys.argv[1] if len(sys.argv) > 1 else None
    storage_filter = int(sys.argv[2]) if len(sys.argv) > 2 else None

    label = f" för '{model_filter}'" if model_filter else " (alla modeller)"
    if storage_filter:
        label += f" {storage_filter}GB"
    print(f"Kör Swappie-scraper{label}...")

    scraper = SwappieScraper()
    prices = await scraper.fetch_prices()

    # Filtrera
    if model_filter:
        prices = [p for p in prices if model_filter.lower() in p["model"].lower()]
    if storage_filter:
        prices = [p for p in prices if p["storage_gb"] == storage_filter]

    if not prices:
        print("Inga priser hittades.")
        return

    # Gruppera per (model, storage)
    by_model_storage: dict = defaultdict(list)
    for p in prices:
        by_model_storage[(p["model"], p["storage_gb"])].append(p)

    print(f"\nTotalt: {len(prices)} priser för {len(by_model_storage)} modell/lagrings-kombinationer")
    print(f"Condition-format: VISUELLT_SKICK  eller  VISUELLT_SKICK:FELKODER")
    print(f"Batterigräns: {BATTERY_THRESHOLD}% (under = BAT-flagga)")

    for (model, storage_gb) in sorted(by_model_storage.keys()):
        model_prices = by_model_storage[(model, storage_gb)]
        storage_label = f"{storage_gb}GB" if storage_gb else "?"
        print(f"\n{'='*65}")
        print(f"  {model} {storage_label}  ({len(model_prices)} kombinationer)")
        print(f"{'='*65}")
        print(f"  {'Condition-nyckel':<30} {'Pris (SEK)':>10}  Beskrivning")
        print(f"  {'-'*60}")

        # Sortera: visuellt skick i VISUAL_ORDER, sedan antal fel (färre fel = bättre)
        def sort_key(p):
            visual, funcs = parse_condition(p["condition"])
            vi = VISUAL_ORDER.index(visual) if visual in VISUAL_ORDER else 99
            return (vi, len(funcs), sorted(funcs))

        for p in sorted(model_prices, key=sort_key):
            visual, funcs = parse_condition(p["condition"])
            func_desc = " + ".join(FUNC_LABELS.get(f, f) for f in sorted(funcs))
            visual_label = VISUAL_LABELS.get(visual, visual)
            desc = visual_label + (f", {func_desc}" if func_desc else "")
            print(f"  {p['condition']:<30} {p['price_sek']:>10}  {desc}")


if __name__ == "__main__":
    asyncio.run(main())
