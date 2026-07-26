import unittest

from app.scrapers.happyphone import _calc_price, _compute_all_prices


IPHONE_XR_CALC = {
    "variations": [
        {
            "storage": "128GB",
            "like_new": "775",
            "very_good": "673",
            "good": "571",
            "acceptable": "458",
        },
        {
            "storage": "256GB",
            "like_new": "100",
            "very_good": "100",
            "good": "100",
            "acceptable": "100",
        },
        {
            "storage": "128GB",
            "like_new": "100",
            "very_good": "100",
            "good": "100",
            "acceptable": "100",
        },
        {
            "storage": "64GB",
            "like_new": "100",
            "very_good": "100",
            "good": "100",
            "acceptable": "100",
        },
    ],
    "ifDisplay": "100",
    "ifWorking": "100",
    "ifBattery": "100",
    "ifCrackedBack": None,
    "lowest": "100",
    "isWaterDamaged": "60",
}


class HappyPhoneNullDeductionTests(unittest.TestCase):
    def test_missing_active_deduction_means_no_offer(self):
        self.assertIsNone(
            _calc_price(
                IPHONE_XR_CALC,
                0,
                "good",
                no_working=False,
                no_display=False,
                no_back=True,
                no_battery=True,
            )
        )

    def test_xr_cracked_back_rows_are_omitted(self):
        rows = _compute_all_prices("iPhone XR", IPHONE_XR_CALC, "iphone-xr")

        self.assertFalse(any("no_back" in row["condition"] for row in rows))
        self.assertIn(
            {
                "model": "iPhone XR",
                "storage_gb": 128,
                "condition": "good:no_battery",
                "price_sek": 471,
                "url": "https://happyphone.se/product/iphone-xr",
            },
            rows,
        )

    def test_duplicate_storage_keeps_highest_base_price_once(self):
        rows = _compute_all_prices("iPhone XR", IPHONE_XR_CALC, "iphone-xr")
        matching = [
            row
            for row in rows
            if row["storage_gb"] == 128 and row["condition"] == "good"
        ]

        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0]["price_sek"], 571)


if __name__ == "__main__":
    unittest.main()
