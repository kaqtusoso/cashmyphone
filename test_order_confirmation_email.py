import unittest

from app.routers.orders import (
    OrderCustomer,
    OrderOut,
    OrderPayment,
    _confirmation_html,
    _confirmation_text,
)


def make_order(shipping_option: str, shipping_label: str) -> OrderOut:
    return OrderOut(
        order_id="TEST-ORDER-123",
        created_at="2026-07-13T12:00:00+00:00",
        model="iPhone 15 Pro",
        storage="256 GB",
        dealer_id="test-dealer",
        dealer_name="Testköparen",
        price_sek=7_500,
        shipping_option=shipping_option,
        shipping_label=shipping_label,
        customer=OrderCustomer(
            first_name="Pascal",
            last_name="Test",
            address="Testgatan 1",
            postal_code="111 11",
            city="Stockholm",
            phone="0700000000",
            email="brjanssonp@gmail.com",
        ),
        payment=OrderPayment(method="swish", label="Swish", swish_number="0700000000"),
        source="televera_web",
    )


class OrderConfirmationEmailTests(unittest.TestCase):
    def test_sales_package_copy(self) -> None:
        order = make_order("sales-package", "Försäljningspaket")
        html = _confirmation_html(order)
        text = _confirmation_text(order)

        self.assertIn("Invänta paket", html)
        self.assertIn("Packa &amp; skicka", html)
        self.assertIn(">Betalning</div>", html)
        self.assertIn("Stäng av Hitta min iPhone", html)
        self.assertNotIn("Du får fraktsedeln och postar mobilen", html)
        self.assertEqual(html.count('class="tv-step-sub"'), 3)
        self.assertIn('/mail-assets/televera-logo-full.png"', html)
        self.assertIn("3. Betalning:", text)
        self.assertEqual(text.count("3. Betalning:"), 1)

    def test_email_label_copy(self) -> None:
        order = make_order("email-label", "Fraktetikett via e-post")
        html = _confirmation_html(order)

        self.assertIn("Fraktetikett via e-post", html)
        self.assertIn("Invänta frakt", html)
        self.assertIn("Packa &amp; lämna", html)
        self.assertIn(">Betalning</div>", html)
        self.assertNotIn("fraktsedeln", html.lower())

    def test_store_dropoff_copy_uses_selected_address(self) -> None:
        order = make_order("store-dropoff", "Inlämning via butik: Hamngatan 37, Stockholm")
        html = _confirmation_html(order)

        self.assertIn("Lämna i butik", html)
        self.assertIn("Inlämning via butik:<br>", html)
        self.assertIn(">Hamngatan 37, Stockholm</span>", html)
        self.assertIn(">Betalning</div>", html)

    def test_unknown_shipping_option_has_safe_fallback(self) -> None:
        order = make_order("other", "Egen fraktlösning")
        html = _confirmation_html(order)

        self.assertIn("Följ instruktionerna", html)
        self.assertIn("Egen fraktlösning", html)
        self.assertEqual(html.count('class="tv-step-sub"'), 3)


if __name__ == "__main__":
    unittest.main()
