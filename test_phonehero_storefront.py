import html
import json
import unittest

from scripts.scrape_phonehero_storefront import _product_url, parse_product_page


class PhoneHeroStorefrontTests(unittest.TestCase):
    def test_product_url_uses_variant_sku(self):
        self.assertEqual(
            _product_url(
                "https://phonehero.se/begagnade-mobiler/Apple/iphone-17-pro",
                "092828423709195912",
            ),
            "https://phonehero.se/begagnade-mobiler/Apple/iphone-17-pro/092828423709195912",
        )

    def test_existing_variant_is_replaced_instead_of_duplicated(self):
        self.assertEqual(
            _product_url(
                "https://phonehero.se/begagnade-mobiler/Apple/iphone-17-pro/092828433712195910",
                "092828423709195912",
            ),
            "https://phonehero.se/begagnade-mobiler/Apple/iphone-17-pro/092828423709195912",
        )

    def test_parsed_offer_keeps_deep_link(self):
        products = [
            {
                "sku": "092828423709195912",
                "name": "Apple iPhone 17 Pro Cosmic Orange 256 GB Ny i kartong Nytt batteri original",
                "variant": "256 GB",
                "condition": "Ny i kartong",
                "color": "Cosmic Orange",
                "price": 13_599,
                "discount": 0,
                "image": "https://example.test/iphone.png",
            }
        ]
        snapshot = {
            "memo": {"name": "deviceselector"},
            "data": {"skusJson": json.dumps(products)},
        }
        page = f'<div wire:snapshot="{html.escape(json.dumps(snapshot), quote=True)}"></div>'

        rows = parse_product_page(
            page,
            "https://phonehero.se/begagnade-mobiler/Apple/iphone-17-pro",
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(
            rows[0]["url"],
            "https://phonehero.se/begagnade-mobiler/Apple/iphone-17-pro/092828423709195912",
        )


if __name__ == "__main__":
    unittest.main()
