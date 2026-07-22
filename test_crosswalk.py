import unittest

from app.pricing.crosswalk import (
    FormAnswers,
    fixiphone_se_condition,
    fixmyphone_condition,
    fixphonepro_condition,
    phonehero_conditions,
    renewed_condition,
    swappie_condition,
    telestore_condition,
)
from app.routers.prices import _phonehero_ignores_battery


class CrosswalkRegressionTests(unittest.TestCase):
    def test_rear_camera_reaches_every_retailer(self):
        answers = FormAnswers(
            screen_surface="LIKE_NEW",
            sides_surface="LIKE_NEW",
            back_surface="LIKE_NEW",
            is_back_camera_broken=True,
        )

        self.assertEqual(swappie_condition(answers), "LIKE_NEW:BBC")
        self.assertEqual(fixmyphone_condition(answers), "like_new:no_working")
        self.assertEqual(telestore_condition(answers), "water_damaged")
        self.assertIn(
            "s=n|b=n|d=cam|c=no|bt=ok",
            phonehero_conditions(answers, model="iPhone 13"),
        )
        self.assertIn(
            "dev=n|d=oth|c=no",
            phonehero_conditions(answers, model="iPhone 16", ignore_battery=True),
        )
        self.assertEqual(renewed_condition(answers), "broken")
        self.assertEqual(fixiphone_se_condition(answers), "d45")
        self.assertEqual(
            fixphonepro_condition(answers),
            "s=n|b=n|d=yes|f=n|bt=ok",
        )

    def test_deep_scratches_are_not_glass_cracks(self):
        answers = FormAnswers(
            screen_surface="GOOD",
            sides_surface="LIKE_NEW",
            back_surface="LIKE_NEW",
            is_glass_scratched=True,
        )

        self.assertEqual(fixmyphone_condition(answers), "good:no_display")
        self.assertEqual(telestore_condition(answers), "bra")
        self.assertIn(
            "s=ms|b=n|d=no|c=no|bt=ok",
            phonehero_conditions(answers, model="iPhone 13"),
        )
        self.assertEqual(renewed_condition(answers), "worn")
        self.assertEqual(fixiphone_se_condition(answers), "d10")
        self.assertEqual(
            fixphonepro_condition(answers),
            "s=ms|b=n|d=no|f=y|bt=ok",
        )

    def test_telestore_counts_back_wear_and_keeps_cracks_separate(self):
        worn_back = FormAnswers("LIKE_NEW", "LIKE_NEW", "GOOD")
        cracked_back = FormAnswers(
            "LIKE_NEW", "LIKE_NEW", "MODERATE",
            is_frame_broken=True,
            is_back_cracked=True,
        )

        self.assertEqual(telestore_condition(worn_back), "bra")
        self.assertEqual(telestore_condition(cracked_back), "nyskick:sidor")

    def test_phonehero_sides_crack_uses_sprickor_for_legacy_family(self):
        answers = FormAnswers(
            "LIKE_NEW", "MODERATE", "LIKE_NEW",
            is_frame_broken=True,
            is_sides_cracked=True,
        )
        self.assertIn(
            "s=n|b=sp|d=no|c=no|bt=ok",
            phonehero_conditions(answers, model="iPhone 13"),
        )

    def test_renewed_rejects_visual_tiers_below_80_percent_battery(self):
        answers = FormAnswers(
            "GOOD", "LIKE_NEW", "LIKE_NEW",
            is_battery_low=True,
            battery_health_percent=79,
        )
        self.assertEqual(renewed_condition(answers), "broken")

    def test_face_id_uses_each_retailers_specific_category(self):
        answers = FormAnswers(
            "LIKE_NEW", "LIKE_NEW", "LIKE_NEW",
            is_broken=True,
            is_face_id_broken=True,
        )
        self.assertIsNone(swappie_condition(answers))
        self.assertEqual(fixmyphone_condition(answers), "water_damaged")
        self.assertIn(
            "s=n|b=n|d=fid|c=no|bt=ok",
            phonehero_conditions(answers, model="iPhone 13"),
        )
        self.assertEqual(fixiphone_se_condition(answers), "d90")

    def test_phonehero_uses_touch_id_answer_for_iphone_se(self):
        answers = FormAnswers(
            "LIKE_NEW", "LIKE_NEW", "LIKE_NEW",
            is_broken=True,
            is_face_id_broken=True,
        )
        self.assertIn(
            "s=n|b=n|d=fp|c=no|bt=ok",
            phonehero_conditions(answers, model="iPhone SE (2022)"),
        )

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
