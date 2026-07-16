import unittest

from scripts.scrape_fixtech_storefront import (
    _parse_condition,
    _validate_inventory_coverage,
    parse_products,
)


class FixTechStorefrontTests(unittest.TestCase):
    def test_nyhet_without_condition_is_unclear(self):
        self.assertEqual(_parse_condition("iPhone 17 Pro Max 256 GB, silver -NYHET", "NYHET"), "Oklart")

    def test_explicit_variant_condition_wins_over_nyhet_ribbon(self):
        self.assertEqual(
            _parse_condition("iPhone 16 Pro Max 256 GB, svart titanium -som ny -batteri 100%", "NYHET"),
            "som ny",
        )

    def test_product_parser_uses_unclear_condition_for_nyhet_variant(self):
        rows = parse_products(
            [
                {
                    "id": "product-1",
                    "title": "Apple iPhone 17 Pro Max 5G smartphone",
                    "slug": "apple-iphone-17-pro-max-5g-smartphone",
                    "ribbon_text": "NYHET",
                    "variants": [
                        {
                            "id": "variant-silver",
                            "sku": "256 GB",
                            "title": "iPhone 17 Pro Max 256 GB, silver -NYHET",
                            "is_available": True,
                            "prices": [{"amount": 1_300_000, "currency_code": "sek"}],
                        }
                    ],
                }
            ]
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["condition_grade"], "Oklart")
        self.assertEqual(rows[0]["price_sek"], 13_000)
        self.assertFalse(rows[0]["inventory_verified"])
        self.assertTrue(rows[0]["variant_deep_link"])
        self.assertFalse(rows[0]["variant_selection_required"])

    def test_product_parser_excludes_variant_with_zero_inventory(self):
        products = [
            {
                "id": "product-1",
                "title": "Apple iPhone 17 Pro Max 5G smartphone",
                "slug": "apple-iphone-17-pro-max-5g-smartphone",
                "ribbon_text": "NYHET",
                "variants": [
                    {
                        "id": "variant-silver",
                        "sku": "256 GB",
                        "title": "iPhone 17 Pro Max 256 GB, silver -NYHET",
                        "is_available": True,
                        "prices": [{"amount": 1_300_000, "currency_code": "sek"}],
                    },
                    {
                        "id": "variant-orange",
                        "sku": "256 GB",
                        "title": "iPhone 17 Pro Max 256 GB, kosmiskt orange -NYHET",
                        "is_available": True,
                        "prices": [{"amount": 1_398_000, "currency_code": "sek"}],
                    },
                ],
            }
        ]

        rows = parse_products(
            products,
            variant_inventory={"variant-silver": 0, "variant-orange": 1},
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["variant_id"], "variant-orange")
        self.assertEqual(rows[0]["stock"], 1)
        self.assertTrue(rows[0]["inventory_verified"])
        self.assertFalse(rows[0]["variant_deep_link"])
        self.assertTrue(rows[0]["variant_selection_required"])

    def test_multiple_stocked_variants_are_marked_as_requiring_selection(self):
        products = [
            {
                "id": "product-1",
                "title": "Apple iPhone 15",
                "slug": "apple-iphone-15",
                "variants": [
                    {
                        "id": "variant-blue",
                        "sku": "128 GB blue",
                        "title": "iPhone 15 128 GB, blue -som ny",
                        "is_available": True,
                        "prices": [{"amount": 700_000, "currency_code": "sek"}],
                    },
                    {
                        "id": "variant-black",
                        "sku": "128 GB black",
                        "title": "iPhone 15 128 GB, black -som ny",
                        "is_available": True,
                        "prices": [{"amount": 710_000, "currency_code": "sek"}],
                    },
                ],
            }
        ]

        rows = parse_products(
            products,
            variant_inventory={"variant-blue": 1, "variant-black": 1},
        )

        self.assertEqual(len(rows), 2)
        self.assertTrue(all(row["variant_selection_required"] for row in rows))
        self.assertTrue(all(not row["variant_deep_link"] for row in rows))

    def test_product_parser_does_not_fall_back_when_inventory_variant_is_missing(self):
        products = [
            {
                "id": "product-1",
                "title": "Apple iPhone 17 Pro Max 5G smartphone",
                "variants": [
                    {
                        "id": "variant-silver",
                        "sku": "256 GB",
                        "title": "iPhone 17 Pro Max 256 GB, silver -NYHET",
                        "is_available": True,
                        "prices": [{"amount": 1_300_000, "currency_code": "sek"}],
                    }
                ],
            }
        ]

        self.assertEqual(parse_products(products, variant_inventory={}), [])

    def test_incomplete_inventory_response_is_rejected(self):
        products = [
            {
                "id": "product-1",
                "variants": [
                    {"id": "variant-a"},
                    {"id": "variant-b"},
                ],
            }
        ]

        with self.assertRaisesRegex(RuntimeError, "missing 1 of 2 variants"):
            _validate_inventory_coverage(products, {"variant-a": 1})


if __name__ == "__main__":
    unittest.main()
