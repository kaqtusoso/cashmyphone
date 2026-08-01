import unittest

from app.scrapers.fixmyphone import _calc_price, _compute_all_prices


IPHONE_SE_2022_CALC = {
    "variations": [
        {
            "storage": "64GB",
            "like_new": "800",
            "very_good": "650",
            "good": "575",
            "acceptable": "533",
        }
    ],
    "ifDisplay": "500",
    "ifWorking": "500",
    "ifBattery": "500",
    "ifCrackedBack": None,
    "lowest": "150",
    "isWaterDamaged": "50",
}


class FixMyPhoneNullDeductionTests(unittest.TestCase):
    def test_missing_active_deduction_means_no_offer(self):
        self.assertIsNone(
            _calc_price(
                IPHONE_SE_2022_CALC,
                0,
                "acceptable",
                no_working=False,
                no_display=False,
                no_back=True,
                no_battery=True,
            )
        )

    def test_se_2022_cracked_back_rows_are_omitted(self):
        rows = _compute_all_prices(
            "iPhone SE 2022", IPHONE_SE_2022_CALC, "iphone-se-2022"
        )

        self.assertTrue(rows)
        self.assertFalse(any("no_back" in row["condition"] for row in rows))
        self.assertIn(
            {
                "model": "iPhone SE 2022",
                "storage_gb": 64,
                "condition": "acceptable:no_battery",
                "price_sek": 150,
                "url": "https://salja.fixmyphone.se/salja/iphone-se-2022",
            },
            rows,
        )

    def test_numeric_cracked_back_deduction_still_produces_an_offer(self):
        calc = {**IPHONE_SE_2022_CALC, "ifCrackedBack": "125"}

        self.assertEqual(
            _calc_price(
                calc,
                0,
                "good",
                no_working=False,
                no_display=False,
                no_back=True,
                no_battery=False,
            ),
            450,
        )


if __name__ == "__main__":
    unittest.main()
