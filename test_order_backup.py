import json
import unittest
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.database import Base
from app.models import OrderSubmissionBackup
from app.routers.orders import (
    IntegrationStatus,
    OrderCreate,
    OrderCustomer,
    OrderOut,
    OrderPayment,
    _store_order_backup,
    _update_order_backup_integrations,
    create_order,
    get_order_backups,
    retry_order_backup_google_sheets,
)


def make_order(order_id: str = "TLV-BACKUPTEST") -> OrderOut:
    return OrderOut(
        order_id=order_id,
        created_at="2026-08-07T10:00:00+00:00",
        model="iPhone 13",
        storage="128 GB",
        color="Midnatt",
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
        condition_answers={"batteryHealth": 91, "functional": ["yes"]},
        source="televera_web",
    )


class OrderBackupTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.session_factory = async_sessionmaker(
            self.engine,
            expire_on_commit=False,
        )
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    async def asyncTearDown(self):
        await self.engine.dispose()

    async def test_backup_preserves_every_submitted_field(self):
        order = make_order()
        with patch("app.routers.orders.AsyncSessionLocal", self.session_factory):
            backup_id = await _store_order_backup(order)

        async with self.session_factory() as session:
            backup = await session.get(OrderSubmissionBackup, backup_id)

        self.assertIsNotNone(backup)
        payload = json.loads(backup.payload_json)
        self.assertEqual(payload, order.model_dump(mode="json"))
        self.assertEqual(payload["customer"]["personal_number"], "200001011234")
        self.assertEqual(payload["payment"]["swish_number"], "0700000000")
        self.assertEqual(payload["condition_answers"]["batteryHealth"], 91)

    async def test_backups_are_append_only_even_for_the_same_order_id(self):
        order = make_order()
        with patch("app.routers.orders.AsyncSessionLocal", self.session_factory):
            first_id = await _store_order_backup(order)
            second_id = await _store_order_backup(order)

        self.assertNotEqual(first_id, second_id)
        async with self.session_factory() as session:
            rows = (
                await session.execute(
                    select(OrderSubmissionBackup).where(
                        OrderSubmissionBackup.order_id == order.order_id
                    )
                )
            ).scalars().all()
        self.assertEqual(len(rows), 2)

    async def test_integration_results_are_saved_with_the_backup(self):
        with patch("app.routers.orders.AsyncSessionLocal", self.session_factory):
            backup_id = await _store_order_backup(make_order())
            await _update_order_backup_integrations(
                backup_id,
                IntegrationStatus(configured=True, ok=False, message="ReadTimeout"),
                IntegrationStatus(configured=True, ok=True, message="Skickat"),
            )

        async with self.session_factory() as session:
            backup = await session.get(OrderSubmissionBackup, backup_id)
        self.assertEqual(backup.google_sheets_status, "failed")
        self.assertEqual(backup.google_sheets_message, "ReadTimeout")
        self.assertEqual(backup.email_status, "delivered")
        self.assertIsNotNone(backup.integration_updated_at)

    async def test_admin_lookup_returns_the_complete_order(self):
        order = make_order()
        with (
            patch("app.routers.orders.AsyncSessionLocal", self.session_factory),
            patch("app.routers.orders.settings.scrape_api_key", "admin-key"),
        ):
            await _store_order_backup(order)
            backups = await get_order_backups(order.order_id, "admin-key")

        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].order, order)

    async def test_admin_lookup_rejects_an_invalid_key(self):
        with patch("app.routers.orders.settings.scrape_api_key", "admin-key"):
            with self.assertRaises(HTTPException) as context:
                await get_order_backups("TLV-BACKUPTEST", "wrong-key")
        self.assertEqual(context.exception.status_code, 401)

    async def test_saved_order_can_be_retried_to_google_sheets(self):
        sheets_status = IntegrationStatus(
            configured=True,
            ok=True,
            message="Order skickad",
        )
        with (
            patch("app.routers.orders.AsyncSessionLocal", self.session_factory),
            patch("app.routers.orders.settings.scrape_api_key", "admin-key"),
            patch(
                "app.routers.orders._send_to_google_sheet",
                new=AsyncMock(return_value=sheets_status),
            ),
        ):
            backup_id = await _store_order_backup(make_order())
            result = await retry_order_backup_google_sheets(
                backup_id,
                "admin-key",
            )

        self.assertTrue(result.ok)
        async with self.session_factory() as session:
            backup = await session.get(OrderSubmissionBackup, backup_id)
        self.assertEqual(backup.google_sheets_status, "delivered")

    async def test_order_is_not_confirmed_when_backup_storage_fails(self):
        payload = OrderCreate.model_validate(
            make_order().model_dump(exclude={"order_id", "created_at"})
        )
        with patch(
            "app.routers.orders._store_order_backup",
            new=AsyncMock(side_effect=RuntimeError("database unavailable")),
        ):
            with self.assertRaises(HTTPException) as context:
                await create_order(payload)

        self.assertEqual(context.exception.status_code, 503)
        self.assertIn("inte registrerats", context.exception.detail)


if __name__ == "__main__":
    unittest.main()
