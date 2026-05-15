"""
Lokal test: kör FixMyPhone-scrapern och visa resultatet.
Kör: python test_fixmyphone.py
      python test_fixmyphone.py "iPhone 16"
      python test_fixmyphone.py "iPhone 16" 256
"""
import asyncio
import sys
import os
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:////tmp/test.db")

from app.scrapers.fixmyphone import FixMyPhoneScraper

# Visningsordning för condition-nycklar
BASE_CONDITIONS = ["like_new", "very_good", "good", "acceptable"]
FAULT_COMBOS = [
    (),
    ("no_working",),
    ("no_display",),
    ("no_back",),
    ("no_battery",),
    ("no_back", "no_battery"),
    ("no_display", "no_battery"),
    ("no_display", "no_back"),
    ("no_working", "no_battery"),
    ("no_working", "no_back"),
    ("no_working", "no_display"),
    ("no_display", "no_back", "no_battery"),
    ("no_working", "no_back", "no_battery"),
    ("no_working", "no_display", "no_battery"),
    ("no_working", "no_display", "no_back"),
    ("no_working", "no_display", "no_back", "no_battery"),
]

def _build_order() -> list[str]:
    order = []
    for base in BASE_CONDITIONS:
        for faults in FAULT_COMBOS:
            if faults:
                key = base + ":" + ":".join(sorted(faults))
            else:
                key = base
            order.append(key)
    order.append("water_damaged")
    return order

CONDITION_ORDER = _build_order()

CONDITION_LABELS = {
    "like_new":                                              "Som ny",
    "like_new:no_working":                                   "Som ny, fungerar ej",
    "like_new:no_display":                                   "Som ny, skärm trasig",
    "like_new:no_back":                                      "Som ny, baksida trasig",
    "like_new:no_battery":                                   "Som ny, batteri lågt",
    "like_new:no_back:no_battery":                           "Som ny, baksida+batteri",
    "like_new:no_battery:no_display":                        "Som ny, skärm+batteri",
    "like_new:no_back:no_display":                           "Som ny, skärm+baksida",
    "like_new:no_battery:no_working":                        "Som ny, fungerar ej+batteri",
    "like_new:no_back:no_working":                           "Som ny, fungerar ej+baksida",
    "like_new:no_display:no_working":                        "Som ny, fungerar ej+skärm",
    "like_new:no_back:no_battery:no_display":                "Som ny, skärm+baksida+bat",
    "like_new:no_back:no_battery:no_working":                "Som ny, ej fungerar+baksida+bat",
    "like_new:no_battery:no_display:no_working":             "Som ny, ej fungerar+skärm+bat",
    "like_new:no_back:no_display:no_working":                "Som ny, ej fungerar+skärm+baksida",
    "like_new:no_back:no_battery:no_display:no_working":     "Som ny, alla fel",
    "very_good":                                             "Mycket bra",
    "very_good:no_working":                                  "Mycket bra, fungerar ej",
    "very_good:no_display":                                  "Mycket bra, skärm trasig",
    "very_good:no_back":                                     "Mycket bra, baksida trasig",
    "very_good:no_battery":                                  "Mycket bra, batteri lågt",
    "very_good:no_back:no_battery":                          "Mycket bra, baksida+batteri",
    "very_good:no_battery:no_display":                       "Mycket bra, skärm+batteri",
    "very_good:no_back:no_display":                          "Mycket bra, skärm+baksida",
    "very_good:no_battery:no_working":                       "Mycket bra, fungerar ej+batteri",
    "very_good:no_back:no_working":                          "Mycket bra, fungerar ej+baksida",
    "very_good:no_display:no_working":                       "Mycket bra, fungerar ej+skärm",
    "very_good:no_back:no_battery:no_display":               "Mycket bra, skärm+baksida+bat",
    "very_good:no_back:no_battery:no_working":               "Mycket bra, ej fungerar+baksida+bat",
    "very_good:no_battery:no_display:no_working":            "Mycket bra, ej fungerar+skärm+bat",
    "very_good:no_back:no_display:no_working":               "Mycket bra, ej fungerar+skärm+baksida",
    "very_good:no_back:no_battery:no_display:no_working":    "Mycket bra, alla fel",
    "good":                                                  "Bra",
    "good:no_working":                                       "Bra, fungerar ej",
    "good:no_display":                                       "Bra, skärm trasig",
    "good:no_back":                                          "Bra, baksida trasig",
    "good:no_battery":                                       "Bra, batteri lågt",
    "good:no_back:no_battery":                               "Bra, baksida+batteri",
    "good:no_battery:no_display":                            "Bra, skärm+batteri",
    "good:no_back:no_display":                               "Bra, skärm+baksida",
    "good:no_battery:no_working":                            "Bra, fungerar ej+batteri",
    "good:no_back:no_working":                               "Bra, fungerar ej+baksida",
    "good:no_display:no_working":                            "Bra, fungerar ej+skärm",
    "good:no_back:no_battery:no_display":                    "Bra, skärm+baksida+bat",
    "good:no_back:no_battery:no_working":                    "Bra, ej fungerar+baksida+bat",
    "good:no_battery:no_display:no_working":                 "Bra, ej fungerar+skärm+bat",
    "good:no_back:no_display:no_working":                    "Bra, ej fungerar+skärm+baksida",
    "good:no_back:no_battery:no_display:no_working":         "Bra, alla fel",
    "acceptable":                                            "Okej",
    "acceptable:no_working":                                 "Okej, fungerar ej",
    "acceptable:no_display":                                 "Okej, skärm trasig",
    "acceptable:no_back":                                    "Okej, baksida trasig",
    "acceptable:no_battery":                                 "Okej, batteri lågt",
    "acceptable:no_back:no_battery":                         "Okej, baksida+batteri",
    "acceptable:no_battery:no_display":                      "Okej, skärm+batteri",
    "acceptable:no_back:no_display":                         "Okej, skärm+baksida",
    "acceptable:no_battery:no_working":                      "Okej, fungerar ej+batteri",
    "acceptable:no_back:no_working":                         "Okej, fungerar ej+baksida",
    "acceptable:no_display:no_working":                      "Okej, fungerar ej+skärm",
    "acceptable:no_back:no_battery:no_display":              "Okej, skärm+baksida+bat",
    "acceptable:no_back:no_battery:no_working":              "Okej, ej fungerar+baksida+bat",
    "acceptable:no_battery:no_display:no_working":           "Okej, ej fungerar+skärm+bat",
    "acceptable:no_back:no_display:no_working":              "Okej, ej fungerar+skärm+baksida",
    "acceptable:no_back:no_battery:no_display:no_working":   "Okej, alla fel",
    "water_damaged":                                         "Böjd/vatten/Face ID trasig",
}


async def main():
    model_filter   = sys.argv[1] if len(sys.argv) > 1 else None
    storage_filter = int(sys.argv[2]) if len(sys.argv) > 2 else None

    label = f" för {model_filter}" if model_filter else " (alla modeller)"
    print(f"Kör FixMyPhone-scraper{label}...")

    scraper = FixMyPhoneScraper()
    prices  = await scraper.fetch_prices()

    if model_filter:
        prices = [p for p in prices if model_filter.lower() in p["model"].lower()]
    if storage_filter:
        prices = [p for p in prices if p["storage_gb"] == storage_filter]

    if not prices:
        print("Inga priser hittades.")
        return

    from collections import defaultdict
    by_model: dict = defaultdict(lambda: defaultdict(dict))
    for p in prices:
        by_model[p["model"]][p["storage_gb"]][p["condition"]] = p["price_sek"]

    storages_all = sorted(set(p["storage_gb"] for p in prices if p["storage_gb"]))

    print(f"\n{'='*70}")
    print(f"  Totalt: {len(prices)} priser för {len(by_model)} modeller")
    print(f"{'='*70}")

    col_w = 10
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
            label = CONDITION_LABELS.get(cond, cond)
            line = f"  {label:<38}"
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
