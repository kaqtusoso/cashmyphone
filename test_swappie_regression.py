import unittest

from app.pricing.crosswalk import FormAnswers, swappie_condition
from app.scrapers.swappie import IPHONE_MODELS, _condition_key, _parse_results


class SwappieRegressionTests(unittest.TestCase):
    def test_model_list_matches_current_sell_flow_boundaries(self):
        self.assertEqual(len(IPHONE_MODELS), 27)
        self.assertIn("iPhone 16e", IPHONE_MODELS)
        self.assertIn("iPhone 17e", IPHONE_MODELS)
        self.assertIn("iPhone 12 mini", IPHONE_MODELS)
        self.assertIn("iPhone 13 mini", IPHONE_MODELS)

        for unsupported in (
            "iPhone 11",
            "iPhone 11 Pro",
            "iPhone 11 Pro Max",
            "iPhone SE 2020",
            "iPhone XR",
            "iPhone XS",
            "iPhone XS Max",
        ):
            self.assertNotIn(unsupported, IPHONE_MODELS)

    def test_broken_api_rows_are_not_imported_as_buyable_offers(self):
        raw_results = [
            {
                "model_name": "iPhone 13 128GB",
                "visual_condition": "LIKE_NEW",
                "functional_condition": ["BROKEN"],
                "price": {"price": 1200, "limit_price": 100},
            },
            {
                "model_name": "iPhone 13 128GB",
                "visual_condition": "LIKE_NEW",
                "functional_condition": ["BATTERY_ISSUE"],
                "price": {"price": 1100, "limit_price": 100},
            },
        ]

        prices = _parse_results(raw_results)

        self.assertEqual([price["condition"] for price in prices], ["LIKE_NEW:BAT"])

    def test_unknown_api_flags_do_not_create_empty_condition_suffixes(self):
        self.assertEqual(_condition_key("GOOD", ["BROKEN_FRAME"]), "GOOD")

    def test_failed_function_check_never_maps_to_swappie(self):
        answers = FormAnswers(
            screen_surface="LIKE_NEW",
            sides_surface="LIKE_NEW",
            back_surface="LIKE_NEW",
            is_broken=True,
        )

        self.assertIsNone(swappie_condition(answers))


if __name__ == "__main__":
    unittest.main()
