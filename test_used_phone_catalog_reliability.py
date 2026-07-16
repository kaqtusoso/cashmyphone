import json
import os
import tempfile
import unittest
from pathlib import Path

from scripts.build_used_phone_catalog import load_offers, validate_variant_links


class UsedPhoneCatalogReliabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.input_dir = Path(self.temp_dir.name)
        self.snapshot = self.input_dir / "fixtech_storefront_latest.json"
        self.marker = self.input_dir / "fixtech_storefront_latest.failed.json"
        self.snapshot.write_text(
            json.dumps(
                [
                    {
                        "retailer": "fixtech",
                        "sku": "256 GB",
                        "model": "iPhone 17 Pro Max",
                        "storage_gb": 256,
                        "condition_grade": "Oklart",
                        "price_sek": 13_000,
                        "stock": 1,
                        "url": "https://fixtech.se/iphone-17-pro-max",
                    }
                ]
            )
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_explicitly_failed_retailer_is_not_reused(self):
        offers, sources = load_offers(self.input_dir, excluded_retailers={"fixtech"})

        self.assertEqual(offers, [])
        self.assertEqual(sources[0]["excluded"], "latest refresh failed")

    def test_newer_failure_marker_quarantines_old_snapshot(self):
        self.marker.write_text("{}")
        snapshot_mtime = self.snapshot.stat().st_mtime
        os.utime(self.marker, (snapshot_mtime + 1, snapshot_mtime + 1))

        offers, sources = load_offers(self.input_dir)

        self.assertEqual(offers, [])
        self.assertEqual(sources[0]["excluded"], "latest refresh failed")

    def test_new_snapshot_supersedes_older_failure_marker(self):
        self.marker.write_text("{}")
        marker_mtime = self.marker.stat().st_mtime
        os.utime(self.snapshot, (marker_mtime + 1, marker_mtime + 1))

        offers, sources = load_offers(self.input_dir)

        self.assertEqual(len(offers), 1)
        self.assertNotIn("excluded", sources[0])

    def test_catalog_rejects_an_unmarked_product_only_link(self):
        offers, _ = load_offers(self.input_dir)

        with self.assertRaisesRegex(RuntimeError, "neither an exact variant URL"):
            validate_variant_links(offers)

    def test_catalog_accepts_a_transparent_selection_warning(self):
        offers, _ = load_offers(self.input_dir)
        offers[0]["variant_selection_required"] = True

        validate_variant_links(offers)


if __name__ == "__main__":
    unittest.main()
