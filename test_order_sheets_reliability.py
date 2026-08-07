import unittest
from unittest.mock import AsyncMock, patch

import httpx

from app.routers.orders import (
    OrderCustomer,
    OrderOut,
    OrderPayment,
    _append_order_to_google_sheet,
    _google_sheets_error_is_retryable,
    _google_sheets_error_message,
    _run_google_sheet_post_write_tasks,
    _send_to_google_sheet_api,
)


def make_order() -> OrderOut:
    return OrderOut(
        order_id="TLV-RETRYTEST",
        created_at="2026-08-07T08:00:00+00:00",
        model="iPhone 13",
        storage="128 GB",
        dealer_id="telestore",
        dealer_name="Telestore",
        price_sek=2_000,
        shipping_option="store-dropoff",
        shipping_label="Inlämning via butik: Testgatan 1",
        customer=OrderCustomer(
            first_name="Test",
            last_name="Person",
            personal_number="200001011234",
            address="Testgatan 1",
            postal_code="123 45",
            city="Teststad",
            phone="0700000000",
            email="test@example.test",
        ),
        payment=OrderPayment(
            method="swish",
            label="Swish",
            swish_number="0700000000",
        ),
        source="televera_web",
    )


class FakeAsyncClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None


class NeverPostClient:
    async def post(self, *args, **kwargs):
        raise AssertionError("append must not run for an existing order")


class OrderSheetsReliabilityTests(unittest.IsolatedAsyncioTestCase):
    def test_blank_timeout_gets_a_useful_error_message(self):
        timeout = httpx.ReadTimeout("")
        self.assertEqual(_google_sheets_error_message(timeout), "ReadTimeout")
        self.assertTrue(_google_sheets_error_is_retryable(timeout))

    def test_only_transient_http_statuses_are_retried(self):
        request = httpx.Request("GET", "https://sheets.googleapis.com")
        retryable = httpx.HTTPStatusError(
            "busy",
            request=request,
            response=httpx.Response(503, request=request),
        )
        permanent = httpx.HTTPStatusError(
            "forbidden",
            request=request,
            response=httpx.Response(403, request=request),
        )
        self.assertTrue(_google_sheets_error_is_retryable(retryable))
        self.assertFalse(_google_sheets_error_is_retryable(permanent))

    async def test_existing_order_is_not_appended_again(self):
        order = make_order()
        with (
            patch(
                "app.routers.orders._ensure_google_sheet_headers",
                new=AsyncMock(),
            ),
            patch(
                "app.routers.orders._google_sheet_order_exists",
                new=AsyncMock(return_value=True),
            ),
        ):
            appended, row_number = await _append_order_to_google_sheet(
                NeverPostClient(),
                "token",
                order,
            )

        self.assertFalse(appended)
        self.assertIsNone(row_number)

    async def test_timeout_is_retried_and_deduplicated(self):
        order = make_order()
        append = AsyncMock(
            side_effect=[
                httpx.ReadTimeout(""),
                (False, None),
            ]
        )
        post_write = AsyncMock()
        retry_sleep = AsyncMock()

        with (
            patch("app.routers.orders.httpx.AsyncClient", FakeAsyncClient),
            patch(
                "app.routers.orders._get_google_access_token",
                new=AsyncMock(return_value="token"),
            ),
            patch("app.routers.orders._append_order_to_google_sheet", new=append),
            patch(
                "app.routers.orders._run_google_sheet_post_write_tasks",
                new=post_write,
            ),
            patch("app.routers.orders.sleep", new=retry_sleep),
            patch("app.routers.orders.settings.google_service_account_json", "{}"),
            patch("app.routers.orders.settings.google_sheets_spreadsheet_id", "sheet-id"),
        ):
            result = await _send_to_google_sheet_api(order)

        self.assertTrue(result.ok)
        self.assertIn("ingen dubblett", result.message)
        self.assertEqual(append.await_count, 2)
        retry_sleep.assert_awaited_once_with(1)
        post_write.assert_awaited_once()

    async def test_metadata_and_formatting_failures_do_not_lose_written_order(self):
        order = make_order()
        with (
            patch(
                "app.routers.orders._get_google_sheet_id",
                new=AsyncMock(side_effect=httpx.ReadTimeout("")),
            ),
            patch(
                "app.routers.orders._migrate_feedback_sheet_layout",
                new=AsyncMock(side_effect=httpx.ReadTimeout("")),
            ),
        ):
            await _run_google_sheet_post_write_tasks(
                NeverPostClient(),
                "token",
                order,
                2,
            )


if __name__ == "__main__":
    unittest.main()
