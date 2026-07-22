import unittest
from itertools import combinations, product

from app.pricing.crosswalk import FormAnswers, swappie_condition
from app.scrapers.swappie import (
    EXPECTED_CONDITIONS_PER_DEVICE,
    IPHONE_MODELS,
    KNOWN_FUNCTIONAL_CONDITIONS,
    KNOWN_VISUAL_CONDITIONS,
    _condition_key,
    _parse_results,
    _validate_api_schema,
)


def _full_api_matrix(model_name="iPhone 15 128GB"):
    flags = sorted(KNOWN_FUNCTIONAL_CONDITIONS)
    rows = []
    for visual in sorted(KNOWN_VISUAL_CONDITIONS):
        for count in range(len(flags) + 1):
            for functional in combinations(flags, count):
                rows.append({
                    "model_name": model_name,
                    "visual_condition": visual,
                    "functional_condition": list(functional),
                    "price": {"price": 1000, "limit_price": 100},
                })
    return rows


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

    def test_all_current_api_flags_are_preserved_in_condition_key(self):
        raw_results = [
            {
                "model_name": "iPhone 13 128GB",
                "visual_condition": "ALMOST_NEW",
                "functional_condition": [
                    "BROKEN",
                    "BATTERY_ISSUE",
                    "BROKEN_BACK_CAMERA",
                    "BROKEN_FRAME",
                    "BROKEN_SCREEN",
                ],
                "price": {"price": 1200, "limit_price": 100},
            },
        ]

        prices = _parse_results(raw_results)

        self.assertEqual(
            [price["condition"] for price in prices],
            ["ALMOST_NEW:B,BAT,BBC,BF,BS"],
        )

    def test_unknown_api_flags_fail_closed(self):
        self.assertIsNone(_condition_key("GOOD", ["FUTURE_DAMAGE_FLAG"]))
        rows = _full_api_matrix()
        rows[0]["functional_condition"] = ["FUTURE_DAMAGE_FLAG"]
        with self.assertRaisesRegex(RuntimeError, "okända flaggor"):
            _validate_api_schema(rows)

    def test_partial_api_matrix_is_rejected(self):
        rows = _full_api_matrix()
        self.assertEqual(len(rows), EXPECTED_CONDITIONS_PER_DEVICE)
        _validate_api_schema(rows)
        with self.assertRaisesRegex(RuntimeError, "ofullständiga enheter"):
            _validate_api_schema(rows[:-1])

    def test_linda_cracked_back_maps_to_official_api_key(self):
        answers = FormAnswers(
            screen_surface="LIKE_NEW",
            sides_surface="ALMOST_NEW",
            back_surface="MODERATE",
            battery_health_percent=89,
            is_frame_broken=True,
        )

        self.assertEqual(swappie_condition(answers), "ALMOST_NEW:BF")

    def test_battery_threshold_matches_official_flow(self):
        base = dict(
            screen_surface="LIKE_NEW",
            sides_surface="LIKE_NEW",
            back_surface="LIKE_NEW",
        )
        self.assertEqual(
            swappie_condition(FormAnswers(**base, battery_health_percent=85)),
            "LIKE_NEW:BAT",
        )
        self.assertEqual(
            swappie_condition(FormAnswers(**base, battery_health_percent=86)),
            "LIKE_NEW",
        )

    def test_every_televera_swappie_combination_has_an_api_key(self):
        api_keys = {
            _condition_key(visual, list(flags))
            for visual in KNOWN_VISUAL_CONDITIONS
            for enabled in product([False, True], repeat=len(KNOWN_FUNCTIONAL_CONDITIONS))
            for flags in [[
                flag
                for flag, is_enabled in zip(sorted(KNOWN_FUNCTIONAL_CONDITIONS), enabled)
                if is_enabled
            ]]
        }
        surfaces = ("LIKE_NEW", "ALMOST_NEW", "GOOD", "MODERATE")
        checked = 0
        for screen, sides, back in product(surfaces, repeat=3):
            for glass, display, frame, camera, low_battery in product(
                [False, True], repeat=5
            ):
                key = swappie_condition(FormAnswers(
                    screen_surface=screen,
                    sides_surface=sides,
                    back_surface=back,
                    is_glass_broken=glass,
                    is_screen_broken=display,
                    is_frame_broken=frame,
                    is_back_camera_broken=camera,
                    is_battery_low=low_battery,
                ))
                self.assertIn(key, api_keys)
                checked += 1
        self.assertEqual(checked, 2048)

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
