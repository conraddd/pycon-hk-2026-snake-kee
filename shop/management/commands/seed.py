"""python manage.py seed --scale 0.01 --yes

Fills the database with synthetic 蛇記冰室 data: shops, the menu, 蛇記 Rewards members and
90 days of orders, including the real-world mess the demo relies on (duplicate members,
free-text sweetness from an old POS). Run it once, on the `production` branch, after `migrate`.
"""
import time
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from shop.menu_data import MENU, SHOPS, SOLD_OUT
from shop.models import MenuItem, Shop
from snakekee import lakebase

SQL_DIR = Path(__file__).resolve().parents[2] / "sql"


class Command(BaseCommand):
    help = "Seed synthetic 蛇記冰室 data (WARNING: deletes all existing shop data)."

    def add_arguments(self, parser):
        parser.add_argument("--scale", type=float, default=0.01,
                            help="1.0 = ~5.5M orders; 0.01 = ~55k orders (default)")
        parser.add_argument("--yes", action="store_true", help="Don't ask for confirmation.")
        parser.add_argument("--any-branch", action="store_true",
                            help="Allow seeding a branch other than 'production'.")

    def handle(self, *args, scale, yes, any_branch, **options):
        branch = lakebase.resolve_branch_id()
        if branch != "production" and not any_branch:
            raise CommandError(f"You're on Lakebase branch '{branch}'. Seed 'production' "
                               f"(LAKEBASE_BRANCH=production) or pass --any-branch.")
        if not yes and input(f"This DELETES all shop data on '{branch}' and reseeds at scale {scale}. "
                             f"Type 'yes': ") != "yes":
            raise CommandError("Aborted.")

        t0 = time.monotonic()
        with transaction.atomic(), connection.cursor() as cur:
            cur.execute("TRUNCATE order_items, orders, customers, menu_items, shops RESTART IDENTITY CASCADE")
            Shop.objects.bulk_create(
                Shop(id=i, name_en=en, name_zh=zh, district=d, seats=s, traffic=t) for i, en, zh, d, s, t in SHOPS)
            cur.execute("SELECT setval(pg_get_serial_sequence('shops', 'id'), (SELECT max(id) FROM shops))")
            MenuItem.objects.bulk_create(
                MenuItem(slug=slug, name_en=en, name_zh=zh, description_en=den, description_zh=dzh,
                         category=cat, price=price, iced_surcharge=iced, iced_only=only, popularity=pop,
                         sort_order=n, is_available=slug not in SOLD_OUT)
                for n, (slug, en, zh, den, dzh, cat, price, iced, only, pop) in enumerate(MENU))
            cur.execute("SELECT set_config('snake_kee.scale', %s, true)", [str(scale)])
            for sql_file in sorted(SQL_DIR.glob("*.sql")):
                t = time.monotonic()
                cur.execute(sql_file.read_text())
                self.stdout.write(f"  {sql_file.name:<32} {time.monotonic() - t:6.1f}s")
        with connection.cursor() as cur:
            cur.execute("ANALYZE")
            cur.execute("SELECT (SELECT count(*) FROM customers), (SELECT count(*) FROM orders), "
                        "(SELECT count(*) FROM order_items)")
            members, orders, lines = cur.fetchone()
        self.stdout.write(self.style.SUCCESS(
            f"Seeded '{branch}': {members:,} members, {orders:,} orders, {lines:,} order lines "
            f"in {time.monotonic() - t0:.0f}s"))
