from django.db import migrations


def remove_hex_dumbbells(apps, schema_editor):
    InventoryItem = apps.get_model('inventory', 'InventoryItem')
    InventoryItem.objects.filter(
        category='dumbbells',
        name__istartswith='Hex Rubber Dumbbell',
    ).delete()


def restore_hex_dumbbells(apps, schema_editor):
    """Reverse: re-create the hex rubber dumbbell rows."""
    InventoryItem = apps.get_model('inventory', 'InventoryItem')
    weights = [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16, 18, 20,
               22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 45, 50]
    for w in weights:
        qty = 4 if w <= 16 else 2
        InventoryItem.objects.create(
            name=f'Hex Rubber Dumbbell {w} kg',
            category='dumbbells',
            weight_kg=w,
            quantity=qty,
            status='good',
            description='Rubber hex dumbbell pair',
        )


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0002_seed_equipment'),
    ]

    operations = [
        migrations.RunPython(remove_hex_dumbbells, restore_hex_dumbbells),
    ]
