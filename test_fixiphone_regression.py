import unittest

from app.pricing.crosswalk import FormAnswers, fixiphone_se_condition
from app.scrapers.fixiphone import (
    _base_prices_from_html,
    _deduction_from_condition,
    _lower_bound_price,
    _upper_bound_price,
)


FIXIPHONE_XR_HTML = """
<div class="popupInformation">
  <div class="pro-details">
    <input name="product-name" value="iPhone XR">
    <button class="product-price" data-price="1100">64GB</button>
    <button class="product-price" data-price="1200">128GB</button>
    <button class="product-price" data-price="1300">256GB</button>
  </div>
</div>
"""


class FixiphoneRegressionTests(unittest.TestCase):
    def test_iphone_xr_cracked_back_and_some_wear_is_95_to_420(self):
        answers = FormAnswers(
            screen_surface="GOOD",
            sides_surface="ALMOST_NEW",
            back_surface="MODERATE",
            is_frame_broken=True,
            is_back_cracked=True,
            battery_health_percent=82,
        )

        condition = fixiphone_se_condition(answers)
        deduction = _deduction_from_condition(condition)

        self.assertEqual(condition, "d65")
        self.assertEqual(_lower_bound_price(1200, deduction), 95)
        self.assertEqual(_upper_bound_price(1200, deduction), 420)

    def test_current_iphone_xr_storage_prices_are_parsed(self):
        rows = _base_prices_from_html(FIXIPHONE_XR_HTML)

        self.assertEqual(
            [(row["storage_gb"], row["base_price_sek"]) for row in rows],
            [(64, 1100), (128, 1200), (256, 1300)],
        )

    def test_unknown_condition_is_rejected(self):
        self.assertIsNone(_deduction_from_condition("d999"))
        self.assertIsNone(_deduction_from_condition("good"))


if __name__ == "__main__":
    unittest.main()
