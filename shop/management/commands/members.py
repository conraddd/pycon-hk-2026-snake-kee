"""python manage.py members chantaiman

Shows 蛇記 Rewards members whose email contains the text, on the current Lakebase branch.
Handy for comparing a branch with production:
    LAKEBASE_BRANCH=production python manage.py members chantaiman
"""
from django.core.management.base import BaseCommand
from django.db.models import Count

from shop.models import Customer
from snakekee import lakebase


class Command(BaseCommand):
    help = "Show 蛇記 Rewards members matching an email (on the current Lakebase branch)."

    def add_arguments(self, parser):
        parser.add_argument("email", help="Part of an email address, e.g. chantaiman")

    def handle(self, *args, email, **options):
        members = (Customer.objects.filter(email__icontains=email.strip())
                   .annotate(order_count=Count("orders")).order_by("id"))
        self.stdout.write(f"🌿 branch '{lakebase.resolve_branch_id()}'\n")
        for m in members:
            self.stdout.write(f"  #{m.id:<7} {m.email!r:<28} {m.name:<20} {m.points:>5} pts  {m.order_count:>3} orders")
        self.stdout.write(f"  {len(members)} member(s)")
