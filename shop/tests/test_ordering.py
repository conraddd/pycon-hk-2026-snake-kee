"""Tests for the QR ordering app.

These run against whatever database Django gives them:
    python manage.py test             -> a brand-new, EMPTY test database (stock Django)
    LAKEBASE=1 python manage.py test  -> this branch's copy of production
so they create the rows they need and never assume the database is empty.
"""
import json
from decimal import Decimal

from django.test import TestCase

from shop.models import Customer, MenuItem, Order, Shop
from shop.views import find_or_join_member


class OrderingTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):  # created once per class, rolled back at the end
        cls.shop = Shop.objects.create(name_en="Test Shop", name_zh="測試店", district="Test", seats=20)
        cls.tea = MenuItem.objects.create(slug="test-milk-tea", name_en="Milk tea", name_zh="奶茶",
                                          category="drink", price=Decimal("22"), iced_surcharge=Decimal("3"))
        cls.toast = MenuItem.objects.create(slug="test-french-toast", name_en="French toast", name_zh="西多士",
                                            category="toast", price=Decimal("32"))

    def order(self, **body):
        return self.client.post("/api/orders", data=json.dumps({"shopId": self.shop.id, **body}),
                                content_type="application/json")


class MenuApiTests(OrderingTestCase):
    def test_menu_lists_available_items(self):
        slugs = [i["slug"] for i in self.client.get(f"/api/menu?shop={self.shop.id}").json()["items"]]
        self.assertIn("test-milk-tea", slugs)


class PlaceOrderTests(OrderingTestCase):
    def test_iced_drink_costs_more(self):
        res = self.order(tableNo=12, items=[{"itemId": self.tea.id, "temperature": "iced", "sweetness": "少甜"}])
        self.assertEqual(res.status_code, 201)
        self.assertEqual(Decimal(res.json()["total"]), Decimal("25"))

    def test_order_total_adds_up(self):
        res = self.order(items=[{"itemId": self.tea.id, "qty": 2}, {"itemId": self.toast.id}])
        self.assertEqual(Order.objects.get(pk=res.json()["orderId"]).total, Decimal("76"))

    def test_empty_order_is_rejected(self):
        self.assertEqual(self.order(items=[]).status_code, 400)

    def test_unknown_item_creates_nothing(self):
        orders_before = Order.objects.count()
        res = self.order(items=[{"itemId": self.tea.id}, {"itemId": 999_999_999}])
        self.assertEqual(res.status_code, 400)
        self.assertEqual(Order.objects.count(), orders_before)


class RewardsTests(OrderingTestCase):
    def test_same_email_finds_the_same_member(self):
        first = find_or_join_member("Repeat.Guest@example.com")
        again = find_or_join_member("repeat.guest@example.com ")
        self.assertEqual(first.pk, again.pk)

    def test_ordering_earns_points(self):
        res = self.order(memberEmail="points@example.com", items=[{"itemId": self.tea.id}])
        self.assertEqual(res.json()["points"], 22)
        self.assertEqual(Customer.objects.get(email="points@example.com").points, 22)
