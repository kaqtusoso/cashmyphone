import html
import json
import unittest

from scripts.scrape_fixmyphone_storefront import _variant_url as fixmyphone_variant_url
from scripts.scrape_happyphone_storefront import (
    _variant_url as happyphone_variant_url,
    parse_product_page as parse_happyphone_product_page,
)
from scripts.scrape_renewed_storefront import _product_url as renewed_product_url
from scripts.scrape_telestore_storefront import _variant_url as telestore_variant_url


class UsedPhoneVariantUrlTests(unittest.TestCase):
    def test_renewed_uses_shopify_variant_id(self):
        self.assertEqual(
            renewed_product_url("begagnad-iphone-12", 47172652368205),
            "https://renewed.se/products/begagnad-iphone-12?variant=47172652368205",
        )

    def test_happyphone_uses_all_woocommerce_attributes(self):
        self.assertEqual(
            happyphone_variant_url(
                "https://happyphone.se/product/iphone-13/",
                {
                    "attribute_pa_color": "rosa",
                    "attribute_pa_kapacitet": "256-gb",
                    "attribute_pa_skick": "klass-b",
                },
            ),
            "https://happyphone.se/product/iphone-13/?attribute_pa_color=rosa&attribute_pa_kapacitet=256-gb&attribute_pa_skick=klass-b",
        )

    def test_happyphone_keeps_first_stocked_duplicate_attribute_combination(self):
        attributes = {
            "attribute_pa_color": "bla",
            "attribute_pa_kapacitet": "256-gb",
            "attribute_pa_skick": "som-ny",
        }
        variants = [
            {
                "variation_id": 101,
                "sku": "first",
                "attributes": attributes,
                "display_price": 5599,
                "display_regular_price": 5599,
                "is_in_stock": True,
                "is_purchasable": True,
                "max_qty": 1,
                "image": {},
            },
            {
                "variation_id": 102,
                "sku": "duplicate",
                "attributes": attributes,
                "display_price": 5699,
                "display_regular_price": 5699,
                "is_in_stock": True,
                "is_purchasable": True,
                "max_qty": 1,
                "image": {},
            },
        ]
        markup = (
            "<h1>iPhone 14 Begagnad</h1>"
            f'<form data-product_variations="{html.escape(json.dumps(variants), quote=True)}"></form>'
        )

        rows = parse_happyphone_product_page(
            markup,
            "https://happyphone.se/product/iphone-14-fornyad-begagnad/",
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["variation_id"], 101)
        self.assertEqual(rows[0]["price_sek"], 5599)

    def test_fixmyphone_uses_all_woocommerce_attributes(self):
        self.assertEqual(
            fixmyphone_variant_url(
                "https://fixmyphone.se/iphone-13-pre-loved/",
                {
                    "attribute_pa_color": "green",
                    "attribute_pa_capacity": "128-gb",
                    "attribute_pa_condition": "good",
                },
            ),
            "https://fixmyphone.se/iphone-13-pre-loved/?attribute_pa_color=green&attribute_pa_capacity=128-gb&attribute_pa_condition=good",
        )

    def test_telestore_reproduces_the_storefront_combination_url(self):
        data = {
            "productURL": "begagnade-mobiler/iphone/iphone-13",
            "optionsTitles": {
                "251": "128GB",
                "257": "Klass C",
                "259": "Midnight",
            },
        }
        combination = {"id": 1788, "optionIDs": [251, 257, 259]}

        self.assertEqual(
            telestore_variant_url(
                data,
                combination,
                "https://telestore.se/begagnade-mobiler/iphone/iphone-13/",
            ),
            "https://telestore.se/begagnade-mobiler/iphone/iphone-13--128gb-midnight-257-1788",
        )


if __name__ == "__main__":
    unittest.main()
