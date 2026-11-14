"""What the kitchen display assumes about our data.

Round 2 of the demo: copy this into the app's tests, fill in KITCHEN_SWEETNESS,
then run it on the empty test database and on a branch of production:
    cp demo/round-2/data_contracts.py shop/tests/test_data_contracts.py
    uv run python manage.py test shop.tests.test_data_contracts
    LAKEBASE=1 uv run python manage.py test shop.tests.test_data_contracts
"""
from collections import Counter

from django.test import TestCase

from shop.models import OrderItem

# The only values the kitchen display understands. Fill this in on stage:
KITCHEN_SWEETNESS = set()  # 👉 {"正常", "少甜", "走甜"}


class KitchenDisplayContractTests(TestCase):
    def test_every_drink_has_a_sweetness_the_kitchen_understands(self):
        self.assertTrue(KITCHEN_SWEETNESS, "Type the sweetness values the kitchen understands first")
        bad = Counter(OrderItem.objects.filter(item__category="drink")
                      .exclude(sweetness__in=KITCHEN_SWEETNESS)
                      .values_list("sweetness", flat=True))
        if bad:
            self.fail(f"Kitchen display can't read these: {dict(bad.most_common())}")
