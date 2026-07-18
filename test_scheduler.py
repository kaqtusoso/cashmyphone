import unittest
from datetime import datetime, timezone

from app.scheduler import (
    USED_PHONE_CATALOG_MISFIRE_GRACE_SECONDS,
    USED_PHONE_CATALOG_STARTUP_DELAY_SECONDS,
    _used_phone_catalog_startup_run_date,
)


class UsedPhoneCatalogSchedulerTests(unittest.TestCase):
    def test_startup_run_date_is_timezone_aware_and_host_independent(self):
        now = datetime(2026, 7, 18, 4, 30, tzinfo=timezone.utc)

        run_date = _used_phone_catalog_startup_run_date(now)

        self.assertEqual(
            run_date,
            datetime(2026, 7, 18, 4, 30, USED_PHONE_CATALOG_STARTUP_DELAY_SECONDS, tzinfo=timezone.utc),
        )
        self.assertIsNotNone(run_date.utcoffset())

    def test_naive_startup_time_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            _used_phone_catalog_startup_run_date(datetime(2026, 7, 18, 4, 30))

    def test_catalog_catch_up_window_covers_overnight_suspension(self):
        self.assertGreaterEqual(USED_PHONE_CATALOG_MISFIRE_GRACE_SECONDS, 12 * 60 * 60)


if __name__ == "__main__":
    unittest.main()
