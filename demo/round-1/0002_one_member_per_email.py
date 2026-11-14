"""Round 1's fix: the hand-written half of the migration.

`makemigrations` writes only the AlterField (the unique index). It can't know that production has
members who signed up twice, or which account to keep. So we write that part ourselves.
On stage, after the red test, replace the generated file with this one:
    cp demo/round-1/0002_one_member_per_email.py shop/migrations/
"""
from django.db import migrations, models
from django.db.models import Case, Value, When
from django.db.models.functions import Lower, Trim


# ⚠️ This migration rewrites data and can't be undone (deleted duplicate members don't come back).
#    That's exactly why we ran it on a Lakebase branch of production first.
def merge_duplicate_members(apps, schema_editor):
    """Production has members who signed up twice. Keep the oldest account per email:
    normalise emails, move orders and points to the account we keep, delete the rest."""
    # Django's foreign keys are DEFERRED: check them now, or Postgres refuses the
    # ALTER TABLE below ("pending trigger events").
    schema_editor.execute("SET CONSTRAINTS ALL IMMEDIATE")
    Customer = apps.get_model("shop", "Customer")
    Order = apps.get_model("shop", "Order")

    Customer.objects.exclude(email=None).update(email=Lower(Trim("email")))

    keep_by_email, keep_for, extra_points = {}, {}, {}
    for member_id, email, points in (Customer.objects.exclude(email=None)
                                     .order_by("id").values_list("id", "email", "points")):
        if email in keep_by_email:  # a later sign-up with the same email -> duplicate
            keep_id = keep_by_email[email]
            keep_for[member_id] = keep_id
            extra_points[keep_id] = extra_points.get(keep_id, 0) + points
        else:
            keep_by_email[email] = member_id
    if not keep_for:
        return

    Order.objects.filter(customer_id__in=keep_for).update(
        customer_id=Case(*[When(customer_id=dup, then=Value(keep)) for dup, keep in keep_for.items()]))
    members = Customer.objects.in_bulk(list(extra_points))
    for keep_id, points in extra_points.items():
        members[keep_id].points += points
    Customer.objects.bulk_update(members.values(), ["points"])
    Customer.objects.filter(id__in=keep_for).delete()
    print(f"\n    merged {len(keep_for)} duplicate members into {len(extra_points)} accounts")


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(merge_duplicate_members, migrations.RunPython.noop),  # 1. fix the data
        migrations.AlterField(                                                     # 2. then add the rule
            model_name='customer',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True, unique=True),
        ),
    ]
