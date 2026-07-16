import unittest

from scripts.build_used_phone_catalog import resolve_battery_health


class UsedPhoneBatteryHealthTests(unittest.TestCase):
    def test_explicit_variant_percentage_is_exact(self):
        self.assertEqual(
            resolve_battery_health("telestore", None, "Klass A", "92%"),
            ("92%", "exact", "retailer_variant"),
        )

    def test_swappie_battery_options_use_current_thresholds(self):
        self.assertEqual(
            resolve_battery_health("swappie", "Standard", "B", None)[:2],
            ("86%", "minimum"),
        )
        self.assertEqual(
            resolve_battery_health("swappie", "Prime", "A", None)[:2],
            ("95%", "minimum"),
        )
        self.assertEqual(
            resolve_battery_health("swappie", "Premium", "A", None)[:2],
            ("100%", "exact"),
        )

    def test_phonehero_distinguishes_guarantee_and_new_battery(self):
        self.assertEqual(
            resolve_battery_health("phonehero", None, "Klass B", None)[:2],
            ("85%", "minimum"),
        )
        self.assertEqual(
            resolve_battery_health("phonehero", "Nytt batteri original", "Klass B", None)[:2],
            ("100%", "exact"),
        )

    def test_renewed_premium_is_100_percent(self):
        self.assertEqual(
            resolve_battery_health("renewed", None, "Premium", None)[:2],
            ("100%", "exact"),
        )
        self.assertEqual(
            resolve_battery_health("renewed", None, "Nyskick", None)[:2],
            ("80%", "minimum"),
        )

    def test_happyphone_uses_conservative_published_guarantee(self):
        self.assertEqual(
            resolve_battery_health("happyphone", None, "Nyskick", None)[:2],
            ("80%", "minimum"),
        )

    def test_unpublished_policy_stays_unknown(self):
        self.assertEqual(
            resolve_battery_health("fixtech", None, "Nyskick", None),
            (None, "unknown", "not_published"),
        )


if __name__ == "__main__":
    unittest.main()
