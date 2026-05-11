from django.db import migrations


MENU_ITEMS = [
    # ── Hot Drinks ─────────────────────────────────────────────────────────────
    {'name': 'Espresso',            'price': '60.00',  'is_active': True},
    {'name': 'Cappuccino',          'price': '80.00',  'is_active': True},
    {'name': 'Masala Chai',         'price': '30.00',  'is_active': True},
    {'name': 'Green Tea',           'price': '40.00',  'is_active': True},
    {'name': 'Black Coffee',        'price': '50.00',  'is_active': True},
    {'name': 'Hot Chocolate',       'price': '70.00',  'is_active': True},

    # ── Cold Drinks ────────────────────────────────────────────────────────────
    {'name': 'Cold Coffee',         'price': '90.00',  'is_active': True},
    {'name': 'Mineral Water 500ml', 'price': '20.00',  'is_active': True},
    {'name': 'Fresh Lime Soda',     'price': '50.00',  'is_active': True},
    {'name': 'Mango Juice',         'price': '60.00',  'is_active': True},
    {'name': 'Iced Tea',            'price': '55.00',  'is_active': True},

    # ── Snacks ─────────────────────────────────────────────────────────────────
    {'name': 'Veg Sandwich',        'price': '70.00',  'is_active': True},
    {'name': 'Protein Bar',         'price': '80.00',  'is_active': True},
    {'name': 'Biscuits (packet)',   'price': '20.00',  'is_active': True},
    {'name': 'Banana',              'price': '15.00',  'is_active': True},
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
