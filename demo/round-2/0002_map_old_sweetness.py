"""Round 2's fix (optional, not shown on stage): map the old POS values to what the kitchen understands.

    cp demo/round-2/0002_map_old_sweetness.py shop/migrations/
    LAKEBASE=1 uv run python manage.py test shop.tests.test_data_contracts   # green
"""
from django.db import migrations

# Free text from the old POS -> what the kitchen display understands.
# (A product decision, agreed with the kitchen: 少少甜 and 半糖 both become 少甜. Can't be undone.)
LEGACY_SWEETNESS = {
    "less": "少甜", "Less Sweet": "少甜", "少甜 ": "少甜", "少少甜": "少甜", "半糖": "少甜",
    "no sugar": "走甜",
}


def normalise_legacy_sweetness(apps, schema_editor):
    OrderItem = apps.get_model("shop", "OrderItem")
    for legacy, value in LEGACY_SWEETNESS.items():
        OrderItem.objects.filter(sweetness=legacy).update(sweetness=value)


class Migration(migrations.Migration):
    dependencies = [("shop", "0001_initial")]
    operations = [migrations.RunPython(normalise_legacy_sweetness, migrations.RunPython.noop)]
