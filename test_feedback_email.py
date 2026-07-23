import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from app.routers.orders import (
    _build_feedback_email,
    _feedback_candidate_is_due,
    _feedback_email_idempotency_key,
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

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def post(self, url, *, headers, json):
        self.__class__.last_headers = headers
        return FakeResponse()


class FeedbackEmailTests(unittest.IsolatedAsyncioTestCase):
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

    async def test_resend_request_includes_idempotency_header_and_returns_id(self):
        FakeAsyncClient.last_headers = None
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


if __name__ == "__main__":
    unittest.main()
