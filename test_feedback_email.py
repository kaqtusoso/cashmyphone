import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from app.routers.orders import (
    FEEDBACK_SHEET_HEADERS,
    SHEET_HEADERS,
    _build_feedback_email,
    _feedback_candidate_is_due,
    _feedback_email_html,
    _feedback_email_idempotency_key,
    _feedback_rows_from_start_order,
    _feedback_sheet_rows,
    _feedback_status_rows,
    _send_feedback_email_resend,
)


def make_row(**overrides):
    row = {
        "order_id": "TLV-TEST123",
        "created_at": "2026-07-23 12:00",
        "first_name": "Anna",
        "model": "iPhone 15",
        "email": "anna@example.test",
        "feedback_email_sent_at": "",
        "feedback_email_status": "",
        "feedback_email_error": "",
        "feedback_email_id": "",
    }
    row.update(overrides)
    return row


class FakeResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {"id": "resend-email-id"}


class FakeAsyncClient:
    last_headers = None
    last_json = None

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def post(self, url, *, headers, json):
        self.__class__.last_headers = headers
        self.__class__.last_json = json
        return FakeResponse()


class FeedbackEmailTests(unittest.IsolatedAsyncioTestCase):
    def test_feedback_columns_live_only_in_feedback_sheet(self):
        self.assertNotIn("Feedbackmail skickat", SHEET_HEADERS)
        self.assertNotIn("Feedbackmail status", SHEET_HEADERS)
        self.assertNotIn("Feedbackmail fel", SHEET_HEADERS)
        self.assertNotIn("Resend mejl-ID", SHEET_HEADERS)
        self.assertEqual(
            FEEDBACK_SHEET_HEADERS,
            [
                "Ordernummer",
                "Feedbackmail skickat",
                "Feedbackmail status",
                "Feedbackmail fel",
                "Resend mejl-ID",
            ],
        )

    def test_feedback_sheet_rows_migrate_legacy_values_and_preserve_existing(self):
        legacy_headers = [
            *SHEET_HEADERS,
            "Feedbackmail skickat",
            "Feedbackmail status",
            "Feedbackmail fel",
            "Resend mejl-ID",
        ]
        first_order = [""] * len(legacy_headers)
        first_order[legacy_headers.index("Ordernummer")] = "TLV-FIRST"
        first_order[legacy_headers.index("Feedbackmail skickat")] = "2026-08-06 09:15"
        first_order[legacy_headers.index("Feedbackmail status")] = "sent"
        first_order[legacy_headers.index("Resend mejl-ID")] = "legacy-id"
        second_order = [""] * len(legacy_headers)
        second_order[legacy_headers.index("Ordernummer")] = "TLV-SECOND"

        rows = _feedback_sheet_rows(
            legacy_headers,
            [first_order, second_order],
            [
                FEEDBACK_SHEET_HEADERS,
                ["TLV-FIRST", "2026-08-06 09:16", "sent", "", "existing-id"],
            ],
        )

        self.assertEqual(rows[0], FEEDBACK_SHEET_HEADERS)
        self.assertEqual(
            rows[1],
            ["TLV-FIRST", "2026-08-06 09:16", "sent", "", "existing-id"],
        )
        self.assertEqual(rows[2], ["TLV-SECOND", "", "", "", ""])
        statuses, row_numbers = _feedback_status_rows(rows)
        self.assertEqual(statuses["TLV-FIRST"]["feedback_email_id"], "existing-id")
        self.assertEqual(row_numbers, {"TLV-FIRST": 2, "TLV-SECOND": 3})

    def test_order_becomes_due_after_fourteen_days(self):
        now = datetime(2026, 8, 6, 12, 0, tzinfo=timezone.utc)
        with (
            patch("app.routers.orders.settings.feedback_email_delay_days", 14),
            patch("app.routers.orders.settings.feedback_email_start_date", "2026-07-23"),
        ):
            self.assertTrue(_feedback_candidate_is_due(make_row(), now))
            self.assertFalse(
                _feedback_candidate_is_due(make_row(created_at="2026-07-23 12:01"), now)
            )

    def test_start_date_prevents_retroactive_backfill(self):
        now = datetime(2026, 8, 6, 12, 0, tzinfo=timezone.utc)
        with (
            patch("app.routers.orders.settings.feedback_email_delay_days", 14),
            patch("app.routers.orders.settings.feedback_email_start_date", "2026-07-23"),
        ):
            self.assertFalse(
                _feedback_candidate_is_due(make_row(created_at="2026-07-22 23:59"), now)
            )

    def test_start_order_id_takes_precedence_over_start_date(self):
        now = datetime(2026, 8, 6, 12, 0, tzinfo=timezone.utc)
        with (
            patch("app.routers.orders.settings.feedback_email_delay_days", 14),
            patch("app.routers.orders.settings.feedback_email_start_date", "2026-07-24"),
            patch(
                "app.routers.orders.settings.feedback_email_start_order_id",
                "TLV-TEST123",
            ),
        ):
            self.assertTrue(
                _feedback_candidate_is_due(
                    make_row(created_at="2026-07-23 12:00"),
                    now,
                )
            )

    def test_rows_begin_at_exact_start_order(self):
        rows = [
            make_row(order_id="TLV-BEFORE"),
            make_row(order_id="TLV-020A6104AB"),
            make_row(order_id="TLV-AFTER"),
        ]
        with patch(
            "app.routers.orders.settings.feedback_email_start_order_id",
            "tlv-020a6104ab",
        ):
            selected, found = _feedback_rows_from_start_order(rows)

        self.assertTrue(found)
        self.assertEqual(
            [row["order_id"] for row in selected],
            ["TLV-020A6104AB", "TLV-AFTER"],
        )

    def test_missing_start_order_fails_closed(self):
        with patch(
            "app.routers.orders.settings.feedback_email_start_order_id",
            "TLV-MISSING",
        ):
            selected, found = _feedback_rows_from_start_order(
                [make_row(order_id="TLV-OTHER")]
            )

        self.assertFalse(found)
        self.assertEqual(selected, [])

    def test_sent_and_in_progress_rows_are_not_selected_again(self):
        now = datetime(2026, 8, 6, 12, 0, tzinfo=timezone.utc)
        with (
            patch("app.routers.orders.settings.feedback_email_delay_days", 14),
            patch("app.routers.orders.settings.feedback_email_start_date", "2026-07-23"),
        ):
            self.assertFalse(
                _feedback_candidate_is_due(
                    make_row(feedback_email_sent_at="2026-08-06 09:15"),
                    now,
                )
            )
            self.assertFalse(
                _feedback_candidate_is_due(
                    make_row(feedback_email_status="sending"),
                    now,
                )
            )

    def test_idempotency_key_is_stable_and_order_specific(self):
        first = _feedback_email_idempotency_key(make_row())
        self.assertEqual(first, _feedback_email_idempotency_key(make_row()))
        self.assertNotEqual(
            first,
            _feedback_email_idempotency_key(make_row(order_id="TLV-OTHER")),
        )

    def test_smtp_message_includes_resend_idempotency_header(self):
        with (
            patch("app.routers.orders.settings.smtp_from_email", "order@televera.se"),
            patch("app.routers.orders.settings.trustpilot_review_url", "https://example.test/review"),
        ):
            message = _build_feedback_email(make_row())
        self.assertEqual(
            message["Resend-Idempotency-Key"],
            _feedback_email_idempotency_key(make_row()),
        )

    def test_selected_design_is_rendered_as_email_safe_html(self):
        with (
            patch("app.routers.orders.settings.public_base_url", "https://api.example.test"),
            patch("app.routers.orders.settings.trustpilot_review_url", "https://example.test/review"),
        ):
            html = _feedback_email_html(make_row(first_name="Anna & Bo"))

        self.assertIn("Vad tyckte du, Anna &amp; Bo?", html)
        self.assertIn("Lämna gärna ett snabbt betyg", html)
        self.assertIn("https://api.example.test/mail-assets/televera-logo-full.png", html)
        self.assertEqual(html.count("aria-label="), 5)
        for stars in range(1, 6):
            self.assertIn(f"https://example.test/review?stars={stars}", html)
            self.assertIn(f"tv-star-cell tv-rating-{stars}", html)
        self.assertIn(
            'class="tv-star-table" role="presentation" dir="rtl"',
            html,
        )
        self.assertIn('dir="ltr" align="center"', html)
        self.assertLess(html.index("review?stars=5"), html.index("review?stars=1"))
        self.assertIn(".tv-rating-3:hover ~ .tv-star-cell .tv-star", html)
        self.assertIn("background:#ff3722 !important", html)
        self.assertIn("background:#ffce00 !important", html)
        self.assertIn("background:#00b67a !important", html)
        self.assertNotIn("Klicka på antal stjärnor", html)
        self.assertNotIn("💚", html)
        self.assertIn('class="tv-bottom-space"', html)
        self.assertIn("border-radius:0 0 20px 20px", html)
        self.assertNotIn("<script", html)
        self.assertNotIn("<x-dc", html)
        self.assertNotIn("<sc-for", html)

    async def test_resend_request_includes_idempotency_header_and_returns_id(self):
        FakeAsyncClient.last_headers = None
        FakeAsyncClient.last_json = None
        with (
            patch("app.routers.orders.httpx.AsyncClient", FakeAsyncClient),
            patch("app.routers.orders.settings.resend_api_key", "re_test"),
            patch("app.routers.orders.settings.smtp_from_email", "order@televera.se"),
            patch("app.routers.orders.settings.trustpilot_review_url", "https://example.test/review"),
        ):
            email_id = await _send_feedback_email_resend(make_row())

        self.assertEqual(email_id, "resend-email-id")
        self.assertEqual(
            FakeAsyncClient.last_headers["Idempotency-Key"],
            _feedback_email_idempotency_key(make_row()),
        )
        self.assertIn("Vad tyckte du, Anna?", FakeAsyncClient.last_json["html"])


if __name__ == "__main__":
    unittest.main()
