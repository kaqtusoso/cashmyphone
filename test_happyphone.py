"""
Lokal test: kör HappyPhone-scrapern och visa resultatet.
Kör: python test_happyphone.py
      python test_happyphone.py "iPhone 16"
      python test_happyphone.py "iPhone 16" 256
"""
import asyncio
import sys
import os
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:////tmp/test.db")

from app.scrapers.happyphone import HappyPhoneScraper

BASE_CONDITIONS = ["like_new", "very_good", "good", "acceptable"]
FAULT_COMBOS = [
    (),
    ("no_working",), ("no_display",), ("no_back",), ("no_battery",),
    ("no_back", "no_battery"), ("no_battery", "no_display"), ("no_back", "no_display"),
    ("no_battery", "no_working"), ("no_back", "no_working"), ("no_display", "no_working"),
    ("no_back", "no_battery", "no_display"), ("no_back", "no_battery", "no_working"),
    ("no_battery", "no_display", "no_working"), ("no_back", "no_display", "no_working"),
    ("no_back", "no_battery", "no_display", "no_working"),
]

def _build_order():
    order = []
    for base in BASE_CONDITIONS:
        for faults in FAULT_COMBOS:
            key = base + (":" + ":".join(sorted(faults)) if faults else "")
            order.append(key)
    order.append("water_damaged")
    return order

CONDITION_ORDER = _build_order()

CONDITION_LABELS = {
    "like_new": "Som ny", "very_good": "Mycket bra", "good": "Bra", "acceptable": "Okej",
    "water_damaged": "Böjd/vatten/Face ID trasig",
}
FAULT_LABELS = {
    "no_working": "fungerar ej", "no_display": "skärm trasig",
    "no_back": "baksida trasig", "no_battery": "batteri lågt",
}

def _label(cond: str) -> str:
    parts = cond.split(":")
    base = CONDITION_LABELS.get(parts[0], parts[0])
    if len(parts) == 1:
        return base
    faults = ", ".join(FAULT_LABELS.get(f, f) for f in parts[1:])
    return f"{base}, {faults}"


async def main():
    model_filter   = sys.argv[1] if len(sys.argv) > 1 else None
    storage_filter = int(sys.argv[2]) if len(sys.argv) > 2 else None

    label = f" för {model_filter}" if model_filter else " (alla modeller)"
    print(f"Kör HappyPhone-scraper{label}...")

    scraper = HappyPhoneScraper()
    prices  = await scraper.fetch_prices()

    if model_filter:
        prices = [p for p in prices if model_filter.lower() in p["model"].lower()]
    if storage_filter:
        prices = [p for p in prices if p["storage_gb"] == storage_filter]

    if not prices:
        print("Inga priser hittades.")
        return

    from collections import defaultdict
    by_model = defaultdict(lambda: defaultdict(dict))
    for p in prices:
        by_model[p["model"]][p["storage_gb"]][p["condition"]] = p["price_sek"]

    col_w = 10
    print(f"\n{'='*70}")
    print(f"  Totalt: {len(prices)} priser för {len(by_model)} modeller")
    print(f"{'='*70}")

    for model in sorted(by_model.keys()):
        storages = sorted(by_model[model].keys())
        print(f"\n{model}")
        header = f"  {'Skick':<38}" + "".join(
            f"{(str(s)+'GB') if s < 1000 else '1TB':>{col_w}}" for s in storages
        )
        print(header)
        print("  " + "-" * (36 + col_w * len(storages)))

        for cond in CONDITION_ORDER:
            row = {s: by_model[model][s].get(cond) for s in storages}
            if not any(v is not None for v in row.values()):
                continue
            line = f"  {_label(cond):<38}"
            for s in storages:
                val = row[s]
                if val is None:
                    line += f"{'–':>{col_w}}"
                elif val <= 100:
                    line += f"{'60 kr*':>{col_w}}"
                else:
                    line += f"{val:>{col_w-3},} kr".replace(",", " ")
            print(line)

    if any(p["price_sek"] <= 100 for p in prices):
        print("\n* 60 kr = böjd, vattenskadad eller Face ID trasig (minimalt bud)")

if __name__ == "__main__":
    asyncio.run(main())
