from django.db import migrations


MENU_ITEMS = [
    # ── Hot Drinks ─────────────────────────────────────────────────────────────
    {'name': 'Espresso',            'price': '60.00',  'is_active': True},
    {'name': 'Americano',           'price': '70.00',  'is_active': True},
    {'name': 'Cappuccino',          'price': '80.00',  'is_active': True},
    {'name': 'Latte',               'price': '90.00',  'is_active': True},
    {'name': 'Masala Chai',         'price': '30.00',  'is_active': True},
    {'name': 'Green Tea',           'price': '40.00',  'is_active': True},

    # ── Cold Drinks ────────────────────────────────────────────────────────────
    {'name': 'Cold Coffee',         'price': '90.00',  'is_active': True},
    {'name': 'Fresh Lime Soda',     'price': '50.00',  'is_active': True},
    {'name': 'Mineral Water',       'price': '20.00',  'is_active': True},
    {'name': 'Orange Juice',        'price': '70.00',  'is_active': True},

    # ── Snacks ─────────────────────────────────────────────────────────────────
    {'name': 'Banana',              'price': '15.00',  'is_active': True},
    {'name': 'Protein Bar',         'price': '80.00',  'is_active': True},
    {'name': 'Granola Bar',         'price': '60.00',  'is_active': True},
    {'name': 'Sandwich',            'price': '70.00',  'is_active': True},
    {'name': 'Salad Bowl',          'price': '120.00', 'is_active': True},
]

SEEDED_NAMES = [item['name'] for item in MENU_ITEMS]


def seed_menu_items(apps, schema_editor):
    MenuItem = apps.get_model('cafe', 'MenuItem')
    for item in MENU_ITEMS:
        MenuItem.objects.get_or_create(name=item['name'], defaults={
            'price': item['price'],
            'is_active': item['is_active'],
        })


def unseed_menu_items(apps, schema_editor):
    MenuItem = apps.get_model('cafe', 'MenuItem')
    MenuItem.objects.filter(name__in=SEEDED_NAMES).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('cafe', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_menu_items, unseed_menu_items),
    ]
