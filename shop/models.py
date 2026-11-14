from django.db import models
from django.utils import timezone


class Shop(models.Model):
    name_en = models.CharField(max_length=80)
    name_zh = models.CharField(max_length=40)
    district = models.CharField(max_length=40)
    seats = models.PositiveSmallIntegerField()
    traffic = models.FloatField(default=1.0, help_text="Relative busyness, used by the seed data.")

    class Meta:
        db_table = "shops"

    def __str__(self):
        return self.name_en


class MenuItem(models.Model):
    class Category(models.TextChoices):
        DRINK = "drink", "Drinks"
        TOAST = "toast", "Toast & buns"
        NOODLES = "noodles", "Noodles"
        RICE = "rice", "Rice"
        SNACK = "snack", "Snacks"

    slug = models.SlugField(unique=True)  # also the image name: /menu/<slug>.svg
    name_en = models.CharField(max_length=80)
    name_zh = models.CharField(max_length=40)
    description_en = models.CharField(max_length=200, blank=True)
    description_zh = models.CharField(max_length=100, blank=True)
    category = models.CharField(max_length=10, choices=Category.choices)
    price = models.DecimalField(max_digits=6, decimal_places=1)
    iced_surcharge = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True,
                                         help_text="Drinks only. NULL = no iced option.")
    iced_only = models.BooleanField(default=False)
    popularity = models.PositiveSmallIntegerField(default=1)
    sort_order = models.PositiveSmallIntegerField(default=0)
    is_available = models.BooleanField(default=True)

    class Meta:
        db_table = "menu_items"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.name_en

    @property
    def is_drink(self):
        return self.category == self.Category.DRINK


class Customer(models.Model):
    """A 蛇記 Rewards member."""

    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    name = models.CharField(max_length=80)
    joined_at = models.DateTimeField(default=timezone.now)
    points = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "customers"

    def __str__(self):
        return f"{self.name} <{self.email}>"


class Order(models.Model):
    class Channel(models.TextChoices):
        DINE_IN = "dine_in", "Dine in"
        TAKEAWAY = "takeaway", "Takeaway"

    class Status(models.TextChoices):
        PLACED = "placed", "Placed"
        PREPARING = "preparing", "Preparing"
        SERVED = "served", "Served"
        PAID = "paid", "Paid"
        CANCELLED = "cancelled", "Cancelled"

    shop = models.ForeignKey(Shop, on_delete=models.PROTECT, related_name="orders")
    customer = models.ForeignKey(Customer, null=True, blank=True, on_delete=models.SET_NULL, related_name="orders")
    table_no = models.PositiveSmallIntegerField(null=True, blank=True)
    channel = models.CharField(max_length=10, choices=Channel.choices, default=Channel.DINE_IN)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PLACED)
    ordered_at = models.DateTimeField(default=timezone.now, db_index=True)
    total = models.DecimalField(max_digits=8, decimal_places=1, default=0)

    class Meta:
        db_table = "orders"
        indexes = [models.Index(fields=["shop", "ordered_at"], name="orders_shop_time_idx")]

    def __str__(self):
        return f"Order #{self.pk}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    item = models.ForeignKey(MenuItem, on_delete=models.PROTECT, related_name="+")
    qty = models.PositiveSmallIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=6, decimal_places=1)
    temperature = models.CharField(max_length=4, blank=True)  # "hot" / "iced" for drinks
    sweetness = models.CharField(max_length=10, blank=True)   # free text from the ordering systems
    ice = models.CharField(max_length=10, blank=True)         # 正常冰 / 少冰 / 走冰 for iced drinks

    class Meta:
        db_table = "order_items"

    def __str__(self):
        return f"{self.qty} x {self.item}"
