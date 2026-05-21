from django.db import migrations

CAFE_INVENTORY = [
    # ── Beverages ──────────────────────────────────────────────────────────
    {'name': 'Mineral Water (500ml)', 'category': 'beverages', 'unit': 'pcs', 'quantity': 48, 'status': 'good', 'description': 'Bottled mineral water'},
    {'name': 'Coca Cola (300ml)', 'category': 'beverages', 'unit': 'pcs', 'quantity': 24, 'status': 'good', 'description': 'Classic Coke cans'},
    {'name': 'Diet Coke (300ml)', 'category': 'beverages', 'unit': 'pcs', 'quantity': 24, 'status': 'good', 'description': 'Diet Coke cans'},
    {'name': 'Red Bull (250ml)', 'category': 'beverages', 'unit': 'pcs', 'quantity': 12, 'status': 'low_stock', 'description': 'Energy drink'},

    # ── Ingredients ────────────────────────────────────────────────────────
    {'name': 'Coffee Beans (Arabica)', 'category': 'ingredients', 'unit': 'kg', 'quantity': 10, 'status': 'good', 'description': 'Medium roast Arabica beans'},
    {'name': 'Whole Milk', 'category': 'ingredients', 'unit': 'L', 'quantity': 20, 'status': 'good', 'description': 'Fresh whole milk for lattes'},
    {'name': 'Oat Milk', 'category': 'ingredients', 'unit': 'L', 'quantity': 5, 'status': 'low_stock', 'description': 'Dairy-free alternative'},
    {'name': 'Sugar (White)', 'category': 'ingredients', 'unit': 'kg', 'quantity': 5, 'status': 'good', 'description': 'Granulated white sugar'},
    {'name': 'Vanilla Syrup', 'category': 'ingredients', 'unit': 'bottle', 'quantity': 4, 'status': 'good', 'description': 'Syrup for flavoring'},
    {'name': 'Caramel Syrup', 'category': 'ingredients', 'unit': 'bottle', 'quantity': 2, 'status': 'low_stock', 'description': 'Syrup for flavoring'},

    # ── Snacks ─────────────────────────────────────────────────────────────
    {'name': 'Chocolate Chip Cookie', 'category': 'snacks', 'unit': 'pcs', 'quantity': 30, 'status': 'good', 'description': 'Freshly baked cookies'},
    {'name': 'Energy Bar (Peanut)', 'category': 'snacks', 'unit': 'pcs', 'quantity': 15, 'status': 'good', 'description': 'High-protein energy bar'},
    {'name': 'Protein Bar (Whey)', 'category': 'snacks', 'unit': 'pcs', 'quantity': 20, 'status': 'good', 'description': 'Gym-special protein bar'},

    # ── Supplies ───────────────────────────────────────────────────────────
    {'name': 'Paper Cups (8oz)', 'category': 'supplies', 'unit': 'pcs', 'quantity': 500, 'status': 'good', 'description': 'Disposable hot drink cups'},
    {'name': 'Cup Lids', 'category': 'supplies', 'unit': 'pcs', 'quantity': 400, 'status': 'good', 'description': 'Plastic lids for paper cups'},
    {'name': 'Napkins (White)', 'category': 'supplies', 'unit': 'pack', 'quantity': 10, 'status': 'good', 'description': '200 napkins per pack'},
    {'name': 'Wooden Stirrers', 'category': 'supplies', 'unit': 'pack', 'quantity': 5, 'status': 'good', 'description': 'Eco-friendly stirrers'},

    # ── Equipment ──────────────────────────────────────────────────────────
    {'name': 'Espresso Machine (2-Group)', 'category': 'equipment', 'unit': 'pcs', 'quantity': 1, 'status': 'good', 'description': 'Commercial espresso machine'},
    {'name': 'Burr Coffee Grinder', 'category': 'equipment', 'unit': 'pcs', 'quantity': 2, 'status': 'good', 'description': 'Professional burr grinder'},
    {'name': 'Milk Frother', 'category': 'equipment', 'unit': 'pcs', 'quantity': 1, 'status': 'maintenance', 'description': 'Steam wand needs cleaning/repair'},
    {'name': 'High-Speed Blender', 'category': 'equipment', 'unit': 'pcs', 'quantity': 2, 'status': 'good', 'description': 'Blender for smoothies'},
]


def seed_cafe_inventory(apps, schema_editor):
    CafeInventoryItem = apps.get_model('cafe', 'CafeInventoryItem')
    for item in CAFE_INVENTORY:
        CafeInventoryItem.objects.create(**item)


def unseed_cafe_inventory(apps, schema_editor):
    CafeInventoryItem = apps.get_model('cafe', 'CafeInventoryItem')
    CafeInventoryItem.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('cafe', '0003_cafeinventoryitem'),
    ]

    operations = [
        migrations.RunPython(seed_cafe_inventory, unseed_cafe_inventory),
    ]
