import unittest

from app.pricing.crosswalk import FormAnswers, fixiphone_se_condition, phonehero_conditions
from app.routers.prices import _phonehero_ignores_battery


class CrosswalkRegressionTests(unittest.TestCase):
    def test_fixiphone_like_new_maps_to_no_deduction(self):
        answers = FormAnswers(
            screen_surface="LIKE_NEW",
            sides_surface="LIKE_NEW",
            back_surface="LIKE_NEW",
        )

        self.assertEqual(fixiphone_se_condition(answers), "d0")

    def test_fixiphone_light_wear_maps_to_unnoticeable_deduction(self):
        answers = FormAnswers(
            screen_surface="GOOD",
            sides_surface="LIKE_NEW",
            back_surface="LIKE_NEW",
        )

        self.assertEqual(fixiphone_se_condition(answers), "d10")

    def test_fixiphone_visible_wear_maps_to_noticeable_deduction(self):
        answers = FormAnswers(
            screen_surface="MODERATE",
            sides_surface="LIKE_NEW",
            back_surface="LIKE_NEW",
        )

        self.assertEqual(fixiphone_se_condition(answers), "d20")

    def test_phonehero_ignores_battery_for_iphone_16_and_newer(self):
        answers = FormAnswers(
            screen_surface="LIKE_NEW",
            sides_surface="LIKE_NEW",
            back_surface="LIKE_NEW",
            is_battery_low=True,
        )

        self.assertTrue(_phonehero_ignores_battery("iPhone 16"))
        self.assertTrue(_phonehero_ignores_battery("iPhone Air"))
        self.assertTrue(_phonehero_ignores_battery("iPhone 17 Pro Max"))
        self.assertEqual(
            phonehero_conditions(answers, ignore_battery=True),
            ["dev=n|d=no|c=no"],
        )

    def test_phonehero_keeps_battery_for_iphone_15_and_older(self):
        answers = FormAnswers(
            screen_surface="LIKE_NEW",
            sides_surface="LIKE_NEW",
            back_surface="LIKE_NEW",
            is_battery_low=True,
        )

        self.assertFalse(_phonehero_ignores_battery("iPhone 15 Pro"))
        self.assertIn("s=n|b=n|d=no|c=no|bt=low", phonehero_conditions(answers))


if __name__ == "__main__":
    unittest.main()
