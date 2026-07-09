#!/usr/bin/env python3
"""
Refresh Televera's buy-side used-phone catalog.

This orchestrates the retailer storefront scrapers and then rebuilds the
normalized catalog used by frontend/API comparison pages.
"""
from __future__ import annotations

import argparse
import asyncio
import importlib
import logging
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.build_used_phone_catalog import (
    DEFAULT_INPUT_DIR,
    DEFAULT_OUTPUT_DIR,
    build_model_summaries,
    load_offers,
    write_csv_catalog,
    write_json_catalog,
)


LOGGER = logging.getLogger("used-phone-catalog-update")

STOREFRONT_SCRAPERS = {
    "fixiphone": "scripts.scrape_fixiphone_storefront",
    "fixmyphone": "scripts.scrape_fixmyphone_storefront",
    "fixtech": "scripts.scrape_fixtech_storefront",
    "happyphone": "scripts.scrape_happyphone_storefront",
    "phonehero": "scripts.scrape_phonehero_storefront",
    "renewed": "scripts.scrape_renewed_storefront",
    "swappie": "scripts.scrape_swappie_storefront",
    "telestore": "scripts.scrape_telestore_storefront",
}


async def refresh_storefront_snapshot(retailer: str) -> dict[str, Any]:
    module_path = STOREFRONT_SCRAPERS[retailer]
    module = importlib.import_module(module_path)

    LOGGER.info("Refreshing %s storefront snapshot", retailer)
    rows = await module.scrape()
    module.write_outputs(rows)
    LOGGER.info("%s storefront snapshot wrote %s rows", retailer, len(rows))
    return {"retailer": retailer, "status": "success", "rows": len(rows)}


def rebuild_catalog(input_dir: Path = DEFAULT_INPUT_DIR, output_dir: Path = DEFAULT_OUTPUT_DIR) -> dict[str, Any]:
    offers, source_files = load_offers(input_dir)
    json_path = write_json_catalog(output_dir, offers, source_files)
    csv_path = write_csv_catalog(output_dir, offers)
    models = build_model_summaries(offers)
    return {
        "status": "success",
        "offers": len(offers),
        "models": len(models),
        "json_path": str(json_path),
        "csv_path": str(csv_path),
        "source_files": source_files,
    }


async def update_used_phone_catalog(
    retailers: list[str] | None = None,
    catalog_only: bool = False,
) -> dict[str, Any]:
    selected_retailers = retailers or list(STOREFRONT_SCRAPERS)
    unknown = sorted(set(selected_retailers) - set(STOREFRONT_SCRAPERS))
    if unknown:
        raise ValueError(f"Unknown storefront retailer(s): {', '.join(unknown)}")

    scraper_results: list[dict[str, Any]] = []
    if not catalog_only:
        for retailer in selected_retailers:
            try:
                scraper_results.append(await refresh_storefront_snapshot(retailer))
            except Exception as exc:
                LOGGER.exception("%s storefront refresh failed", retailer)
                scraper_results.append(
                    {
                        "retailer": retailer,
                        "status": "error",
                        "error": str(exc),
                        "error_type": type(exc).__name__,
                    }
                )

    catalog_result = rebuild_catalog()
    return {
        "status": "completed",
        "scrapers": scraper_results,
        "catalog": catalog_result,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh buy-side used-phone catalog snapshots")
    parser.add_argument(
        "--retailer",
        action="append",
        choices=sorted(STOREFRONT_SCRAPERS),
        help="Refresh one retailer. Can be passed multiple times. Defaults to all retailers.",
    )
    parser.add_argument(
        "--catalog-only",
        action="store_true",
        help="Skip live storefront scraping and rebuild the combined catalog from existing snapshots.",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    result = asyncio.run(update_used_phone_catalog(retailers=args.retailer, catalog_only=args.catalog_only))
    catalog = result["catalog"]
    print(f"Wrote {catalog['offers']} offers across {catalog['models']} models")
    print(f"JSON: {catalog['json_path']}")
    print(f"CSV: {catalog['csv_path']}")
    errors = [scraper for scraper in result["scrapers"] if scraper["status"] != "success"]
    if errors:
        print(f"Completed with {len(errors)} scraper error(s)")
        for error in errors:
            print(f"  {error['retailer']}: {error['error_type']} - {error['error']}")


if __name__ == "__main__":
    main()
