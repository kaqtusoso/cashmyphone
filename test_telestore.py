"""
Lokal test: kör Telestore-scrapern och visa resultatet.
Kör: python test_telestore.py
      python test_telestore.py "iPhone 16"
      python test_telestore.py "iPhone 16" 256
"""
import asyncio
import sys
import os
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:////tmp/test.db")

from app.scrapers.telestore import TelestoreScraper

CONDITION_ORDER = [
    "nyskick", "nyskick:bat", "nyskick:sidor", "nyskick:bat:sidor",
    "utmarkt", "utmarkt:bat", "utmarkt:sidor", "utmarkt:bat:sidor",
    "bra", "bra:bat", "bra:sidor", "bra:bat:sidor",
    "okej", "okej:bat", "okej:sidor", "okej:bat:sidor",
    "sprickor_fram", "sprickor_fram:bat", "sprickor_fram:sidor", "sprickor_fram:bat:sidor",
]

CONDITION_LABELS = {
    "nyskick":                   "Nyskick",
    "nyskick:bat":               "Nyskick, batteri lågt",
    "nyskick:sidor":             "Nyskick, sidor trasiga",
    "nyskick:bat:sidor":         "Nyskick, batteri+sidor",
    "utmarkt":                   "Utmärkt",
    "utmarkt:bat":               "Utmärkt, batteri lågt",
    "utmarkt:sidor":             "Utmärkt, sidor trasiga",
    "utmarkt:bat:sidor":         "Utmärkt, batteri+sidor",
    "bra":                       "Bra",
    "bra:bat":                   "Bra, batteri lågt",
    "bra:sidor":                 "Bra, sidor trasiga",
    "bra:bat:sidor":             "Bra, batteri+sidor",
    "okej":                      "Okej",
    "okej:bat":                  "Okej, batteri lågt",
    "okej:sidor":                "Okej, sidor trasiga",
    "okej:bat:sidor":            "Okej, batteri+sidor",
    "sprickor_fram":             "Sprickor fram",
    "sprickor_fram:bat":         "Sprickor fram, batteri lågt",
    "sprickor_fram:sidor":       "Sprickor fram, sidor trasiga",
    "sprickor_fram:bat:sidor":   "Sprickor fram, batteri+sidor",
}


async def main():
    model_filter   = sys.argv[1] if len(sys.argv) > 1 else None
    storage_filter = int(sys.argv[2]) if len(sys.argv) > 2 else None

    print(f"Kör Telestore-scraper{f' för {model_filter}' if model_filter else ' (alla modeller)'}...")
    scraper = TelestoreScraper()
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

    all_storages = sorted(set(p["storage_gb"] for p in prices if p["storage_gb"]))

    print(f"\n{'='*60}")
    print(f"  Totalt: {len(prices)} priser för {len(by_model)} modeller")
    print(f"{'='*60}")

    for model in sorted(by_model.keys()):
        storages = sorted(by_model[model].keys())
        print(f"\n{model}")

        col_w = 10
        header = f"  {'Skick':<26}" + "".join(
            f"{(str(s)+'GB') if s < 1000 else '1TB':>{col_w}}" for s in storages
        )
        print(header)
        print("  " + "-" * (24 + col_w * len(storages)))

        for cond in CONDITION_ORDER:
            row = {}
            for s in storages:
                row[s] = by_model[model][s].get(cond)
            if not any(v is not None for v in row.values()):
                continue
            label = CONDITION_LABELS.get(cond, cond)
            line = f"  {label:<26}"
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
        print("\n* 60 kr = telefonen köps men till minimalt bud")

if __name__ == "__main__":
    asyncio.run(main())
