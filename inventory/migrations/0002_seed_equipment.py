from django.db import migrations


EQUIPMENT = [
    # ── Dumbbells ──────────────────────────────────────────────────────────────
    # Hex rubber dumbbells (full range)
    {'name': 'Hex Rubber Dumbbell 1 kg',   'category': 'dumbbells', 'weight_kg': 1,    'quantity': 4, 'status': 'good', 'description': 'Rubber hex dumbbell pair'},
    {'name': 'Hex Rubber Dumbbell 2 kg',   'category': 'dumbbells', 'weight_kg': 2,    'quantity': 4, 'status': 'good', 'description': 'Rubber hex dumbbell pair'},
    {'name': 'Hex Rubber Dumbbell 3 kg',   'category': 'dumbbells', 'weight_kg': 3,    'quantity': 4, 'status': 'good', 'description': 'Rubber hex dumbbell pair'},
    {'name': 'Hex Rubber Dumbbell 4 kg',   'category': 'dumbbells', 'weight_kg': 4,    'quantity': 4, 'status': 'good', 'description': 'Rubber hex dumbbell pair'},
    {'name': 'Hex Rubber Dumbbell 5 kg',   'category': 'dumbbells', 'weight_kg': 5,    'quantity': 4, 'status': 'good', 'description': 'Rubber hex dumbbell pair'},
    {'name': 'Hex Rubber Dumbbell 6 kg',   'category': 'dumbbells', 'weight_kg': 6,    'quantity': 4, 'status': 'good', 'description': 'Rubber hex dumbbell pair'},
    {'name': 'Hex Rubber Dumbbell 7 kg',   'category': 'dumbbells', 'weight_kg': 7,    'quantity': 4, 'status': 'good', 'description': 'Rubber hex dumbbell pair'},
    {'name': 'Hex Rubber Dumbbell 8 kg',   'category': 'dumbbells', 'weight_kg': 8,    'quantity': 4, 'status': 'good', 'description': 'Rubber hex dumbbell pair'},
    {'name': 'Hex Rubber Dumbbell 10 kg',  'category': 'dumbbells', 'weight_kg': 10,   'quantity': 4, 'status': 'good', 'description': 'Rubber hex dumbbell pair'},
    {'name': 'Hex Rubber Dumbbell 12 kg',  'category': 'dumbbells', 'weight_kg': 12,   'quantity': 4, 'status': 'good', 'description': 'Rubber hex dumbbell pair'},
    {'name': 'Hex Rubber Dumbbell 14 kg',  'category': 'dumbbells', 'weight_kg': 14,   'quantity': 4, 'status': 'good', 'description': 'Rubber hex dumbbell pair'},
    {'name': 'Hex Rubber Dumbbell 16 kg',  'category': 'dumbbells', 'weight_kg': 16,   'quantity': 4, 'status': 'good', 'description': 'Rubber hex dumbbell pair'},
    {'name': 'Hex Rubber Dumbbell 18 kg',  'category': 'dumbbells', 'weight_kg': 18,   'quantity': 2, 'status': 'good', 'description': 'Rubber hex dumbbell pair'},
    {'name': 'Hex Rubber Dumbbell 20 kg',  'category': 'dumbbells', 'weight_kg': 20,   'quantity': 2, 'status': 'good', 'description': 'Rubber hex dumbbell pair'},
    {'name': 'Hex Rubber Dumbbell 22 kg',  'category': 'dumbbells', 'weight_kg': 22,   'quantity': 2, 'status': 'good', 'description': 'Rubber hex dumbbell pair'},
    {'name': 'Hex Rubber Dumbbell 24 kg',  'category': 'dumbbells', 'weight_kg': 24,   'quantity': 2, 'status': 'good', 'description': 'Rubber hex dumbbell pair'},
    {'name': 'Hex Rubber Dumbbell 26 kg',  'category': 'dumbbells', 'weight_kg': 26,   'quantity': 2, 'status': 'good', 'description': 'Rubber hex dumbbell pair'},
    {'name': 'Hex Rubber Dumbbell 28 kg',  'category': 'dumbbells', 'weight_kg': 28,   'quantity': 2, 'status': 'good', 'description': 'Rubber hex dumbbell pair'},
    {'name': 'Hex Rubber Dumbbell 30 kg',  'category': 'dumbbells', 'weight_kg': 30,   'quantity': 2, 'status': 'good', 'description': 'Rubber hex dumbbell pair'},
    {'name': 'Hex Rubber Dumbbell 32 kg',  'category': 'dumbbells', 'weight_kg': 32,   'quantity': 2, 'status': 'good', 'description': 'Rubber hex dumbbell pair'},
    {'name': 'Hex Rubber Dumbbell 34 kg',  'category': 'dumbbells', 'weight_kg': 34,   'quantity': 2, 'status': 'good', 'description': 'Rubber hex dumbbell pair'},
    {'name': 'Hex Rubber Dumbbell 36 kg',  'category': 'dumbbells', 'weight_kg': 36,   'quantity': 2, 'status': 'good', 'description': 'Rubber hex dumbbell pair'},
    {'name': 'Hex Rubber Dumbbell 38 kg',  'category': 'dumbbells', 'weight_kg': 38,   'quantity': 2, 'status': 'good', 'description': 'Rubber hex dumbbell pair'},
    {'name': 'Hex Rubber Dumbbell 40 kg',  'category': 'dumbbells', 'weight_kg': 40,   'quantity': 2, 'status': 'good', 'description': 'Rubber hex dumbbell pair'},
    {'name': 'Hex Rubber Dumbbell 45 kg',  'category': 'dumbbells', 'weight_kg': 45,   'quantity': 2, 'status': 'good', 'description': 'Rubber hex dumbbell pair'},
    {'name': 'Hex Rubber Dumbbell 50 kg',  'category': 'dumbbells', 'weight_kg': 50,   'quantity': 2, 'status': 'good', 'description': 'Rubber hex dumbbell pair'},
    # Adjustable dumbbells
    {'name': 'Adjustable Dumbbell Set (2.5–25 kg)', 'category': 'dumbbells', 'weight_kg': None, 'quantity': 2, 'status': 'good', 'description': 'Dial-select adjustable dumbbell, 2.5 kg to 25 kg'},
    {'name': 'Adjustable Dumbbell Set (5–52.5 kg)', 'category': 'dumbbells', 'weight_kg': None, 'quantity': 2, 'status': 'good', 'description': 'Dial-select adjustable dumbbell, 5 kg to 52.5 kg'},

    # ── Barbells & Bars ────────────────────────────────────────────────────────
    {'name': 'Olympic Barbell (20 kg)',        'category': 'barbells', 'weight_kg': 20,   'quantity': 6, 'status': 'good',        'description': 'Standard 7-ft Olympic barbell, 20 kg, 28 mm knurl'},
    {'name': 'Women\'s Olympic Barbell (15 kg)', 'category': 'barbells', 'weight_kg': 15, 'quantity': 4, 'status': 'good',        'description': '6-ft women\'s Olympic barbell, 15 kg, 25 mm knurl'},
    {'name': 'EZ Curl Bar',                    'category': 'barbells', 'weight_kg': 10,   'quantity': 4, 'status': 'good',        'description': 'EZ curl bar for bicep and tricep exercises'},
    {'name': 'Tricep Bar (Football Bar)',       'category': 'barbells', 'weight_kg': 9,    'quantity': 2, 'status': 'good',        'description': 'Parallel-grip football bar for pressing and rows'},
    {'name': 'Hex / Trap Bar',                 'category': 'barbells', 'weight_kg': 25,   'quantity': 2, 'status': 'good',        'description': 'Hex trap bar for deadlifts and shrugs'},
    {'name': 'Safety Squat Bar',               'category': 'barbells', 'weight_kg': 25,   'quantity': 2, 'status': 'good',        'description': 'Cambered safety squat bar with shoulder pads'},
    {'name': 'Swiss / Multi-Grip Bar',         'category': 'barbells', 'weight_kg': 20,   'quantity': 2, 'status': 'good',        'description': 'Multi-grip neutral-grip bar'},
    {'name': 'Cambered Bar',                   'category': 'barbells', 'weight_kg': 20,   'quantity': 1, 'status': 'good',        'description': 'Cambered bench press bar'},
    {'name': 'Standard Barbell (15 kg)',       'category': 'barbells', 'weight_kg': 15,   'quantity': 4, 'status': 'good',        'description': 'Standard 1-inch barbell for beginners'},
    {'name': 'Fixed Barbell 10 kg',            'category': 'barbells', 'weight_kg': 10,   'quantity': 2, 'status': 'good',        'description': 'Pre-loaded fixed barbell'},
    {'name': 'Fixed Barbell 20 kg',            'category': 'barbells', 'weight_kg': 20,   'quantity': 2, 'status': 'good',        'description': 'Pre-loaded fixed barbell'},
    {'name': 'Fixed Barbell 30 kg',            'category': 'barbells', 'weight_kg': 30,   'quantity': 2, 'status': 'good',        'description': 'Pre-loaded fixed barbell'},
    {'name': 'Fixed Barbell 40 kg',            'category': 'barbells', 'weight_kg': 40,   'quantity': 2, 'status': 'good',        'description': 'Pre-loaded fixed barbell'},
    {'name': 'Fixed Barbell 50 kg',            'category': 'barbells', 'weight_kg': 50,   'quantity': 2, 'status': 'good',        'description': 'Pre-loaded fixed barbell'},
    {'name': 'Fixed Barbell 60 kg',            'category': 'barbells', 'weight_kg': 60,   'quantity': 2, 'status': 'good',        'description': 'Pre-loaded fixed barbell'},

    # ── Weight Plates ──────────────────────────────────────────────────────────
    {'name': 'Olympic Bumper Plate 5 kg',      'category': 'weight_plates', 'weight_kg': 5,    'quantity': 10, 'status': 'good', 'description': 'Rubber bumper plate, 50 mm bore'},
    {'name': 'Olympic Bumper Plate 10 kg',     'category': 'weight_plates', 'weight_kg': 10,   'quantity': 10, 'status': 'good', 'description': 'Rubber bumper plate, 50 mm bore'},
    {'name': 'Olympic Bumper Plate 15 kg',     'category': 'weight_plates', 'weight_kg': 15,   'quantity': 8,  'status': 'good', 'description': 'Rubber bumper plate, 50 mm bore'},
    {'name': 'Olympic Bumper Plate 20 kg',     'category': 'weight_plates', 'weight_kg': 20,   'quantity': 8,  'status': 'good', 'description': 'Rubber bumper plate, 50 mm bore'},
    {'name': 'Olympic Bumper Plate 25 kg',     'category': 'weight_plates', 'weight_kg': 25,   'quantity': 6,  'status': 'good', 'description': 'Rubber bumper plate, 50 mm bore'},
    {'name': 'Cast Iron Plate 1.25 kg',        'category': 'weight_plates', 'weight_kg': 1.25, 'quantity': 16, 'status': 'good', 'description': 'Cast iron Olympic plate'},
    {'name': 'Cast Iron Plate 2.5 kg',         'category': 'weight_plates', 'weight_kg': 2.5,  'quantity': 16, 'status': 'good', 'description': 'Cast iron Olympic plate'},
    {'name': 'Cast Iron Plate 5 kg',           'category': 'weight_plates', 'weight_kg': 5,    'quantity': 16, 'status': 'good', 'description': 'Cast iron Olympic plate'},
    {'name': 'Cast Iron Plate 10 kg',          'category': 'weight_plates', 'weight_kg': 10,   'quantity': 12, 'status': 'good', 'description': 'Cast iron Olympic plate'},
    {'name': 'Cast Iron Plate 15 kg',          'category': 'weight_plates', 'weight_kg': 15,   'quantity': 8,  'status': 'good', 'description': 'Cast iron Olympic plate'},
    {'name': 'Cast Iron Plate 20 kg',          'category': 'weight_plates', 'weight_kg': 20,   'quantity': 8,  'status': 'good', 'description': 'Cast iron Olympic plate'},
    {'name': 'Cast Iron Plate 25 kg',          'category': 'weight_plates', 'weight_kg': 25,   'quantity': 6,  'status': 'good', 'description': 'Cast iron Olympic plate'},
    {'name': 'Fractional Plate Set (0.25–1 kg)', 'category': 'weight_plates', 'weight_kg': None, 'quantity': 4, 'status': 'good', 'description': 'Micro-loading fractional plates'},

    # ── Cardio Machines ────────────────────────────────────────────────────────
    {'name': 'Treadmill (Commercial)',         'category': 'cardio', 'weight_kg': None, 'quantity': 6, 'status': 'good',        'description': 'Commercial treadmill, 0–22 km/h, 15% incline'},
    {'name': 'Treadmill (Commercial)',         'category': 'cardio', 'weight_kg': None, 'quantity': 2, 'status': 'maintenance', 'description': 'Commercial treadmill — belt replacement due'},
    {'name': 'Upright Exercise Bike',          'category': 'cardio', 'weight_kg': None, 'quantity': 4, 'status': 'good',        'description': 'Upright stationary bike, 32 resistance levels'},
    {'name': 'Recumbent Exercise Bike',        'category': 'cardio', 'weight_kg': None, 'quantity': 2, 'status': 'good',        'description': 'Recumbent bike, low-impact cardio'},
    {'name': 'Spin Bike',                      'category': 'cardio', 'weight_kg': None, 'quantity': 8, 'status': 'good',        'description': 'Indoor cycling spin bike'},
    {'name': 'Elliptical Cross Trainer',       'category': 'cardio', 'weight_kg': None, 'quantity': 4, 'status': 'good',        'description': 'Elliptical trainer, 20 resistance levels'},
    {'name': 'Rowing Machine',                 'category': 'cardio', 'weight_kg': None, 'quantity': 3, 'status': 'good',        'description': 'Air resistance rowing ergometer'},
    {'name': 'Stair Climber',                  'category': 'cardio', 'weight_kg': None, 'quantity': 2, 'status': 'good',        'description': 'Step mill stair climber'},
    {'name': 'Ski Erg',                        'category': 'cardio', 'weight_kg': None, 'quantity': 2, 'status': 'good',        'description': 'Air resistance ski ergometer'},
    {'name': 'Air Assault Bike',               'category': 'cardio', 'weight_kg': None, 'quantity': 3, 'status': 'good',        'description': 'Fan bike, full-body cardio'},

    # ── Strength Machines ──────────────────────────────────────────────────────
    {'name': 'Power Rack / Squat Cage',        'category': 'strength', 'weight_kg': None, 'quantity': 4, 'status': 'good',        'description': 'Full power rack with pull-up bar and safety bars'},
    {'name': 'Half Rack',                      'category': 'strength', 'weight_kg': None, 'quantity': 2, 'status': 'good',        'description': 'Half rack with spotter arms'},
    {'name': 'Smith Machine',                  'category': 'strength', 'weight_kg': None, 'quantity': 2, 'status': 'good',        'description': 'Counter-balanced Smith machine'},
    {'name': 'Flat Bench',                     'category': 'strength', 'weight_kg': None, 'quantity': 6, 'status': 'good',        'description': 'Flat utility bench'},
    {'name': 'Adjustable Bench',               'category': 'strength', 'weight_kg': None, 'quantity': 6, 'status': 'good',        'description': 'FID adjustable bench, flat/incline/decline'},
    {'name': 'Preacher Curl Bench',            'category': 'strength', 'weight_kg': None, 'quantity': 2, 'status': 'good',        'description': 'Preacher curl station'},
    {'name': 'Cable Crossover Machine',        'category': 'strength', 'weight_kg': None, 'quantity': 2, 'status': 'good',        'description': 'Dual-pulley cable crossover'},
    {'name': 'Lat Pulldown / Low Row Machine', 'category': 'strength', 'weight_kg': None, 'quantity': 3, 'status': 'good',        'description': 'Lat pulldown with low row attachment'},
    {'name': 'Leg Press Machine',              'category': 'strength', 'weight_kg': None, 'quantity': 2, 'status': 'good',        'description': '45° plate-loaded leg press'},
    {'name': 'Leg Extension Machine',          'category': 'strength', 'weight_kg': None, 'quantity': 2, 'status': 'good',        'description': 'Seated leg extension'},
    {'name': 'Leg Curl Machine',               'category': 'strength', 'weight_kg': None, 'quantity': 2, 'status': 'good',        'description': 'Lying leg curl'},
    {'name': 'Seated Calf Raise Machine',      'category': 'strength', 'weight_kg': None, 'quantity': 1, 'status': 'good',        'description': 'Seated calf raise'},
    {'name': 'Chest Press Machine',            'category': 'strength', 'weight_kg': None, 'quantity': 2, 'status': 'good',        'description': 'Selectorized chest press'},
    {'name': 'Shoulder Press Machine',         'category': 'strength', 'weight_kg': None, 'quantity': 2, 'status': 'good',        'description': 'Selectorized shoulder press'},
    {'name': 'Pec Deck / Fly Machine',         'category': 'strength', 'weight_kg': None, 'quantity': 2, 'status': 'good',        'description': 'Pec deck butterfly machine'},
    {'name': 'Seated Row Machine',             'category': 'strength', 'weight_kg': None, 'quantity': 2, 'status': 'good',        'description': 'Selectorized seated row'},
    {'name': 'Hack Squat Machine',             'category': 'strength', 'weight_kg': None, 'quantity': 1, 'status': 'good',        'description': 'Plate-loaded hack squat'},
    {'name': 'Glute Ham Developer (GHD)',      'category': 'strength', 'weight_kg': None, 'quantity': 2, 'status': 'good',        'description': 'GHD for back extensions and glute-ham raises'},
    {'name': 'Hyperextension Bench',           'category': 'strength', 'weight_kg': None, 'quantity': 2, 'status': 'good',        'description': '45° hyperextension bench'},
    {'name': 'Dip / Pull-up Station',          'category': 'strength', 'weight_kg': None, 'quantity': 3, 'status': 'good',        'description': 'Freestanding dip and pull-up tower'},
    {'name': 'Functional Trainer',             'category': 'strength', 'weight_kg': None, 'quantity': 2, 'status': 'maintenance', 'description': 'Dual-stack functional trainer — cable inspection due'},

    # ── Accessories ────────────────────────────────────────────────────────────
    {'name': 'Kettlebell 8 kg',                'category': 'accessories', 'weight_kg': 8,    'quantity': 4, 'status': 'good', 'description': 'Cast iron kettlebell'},
    {'name': 'Kettlebell 12 kg',               'category': 'accessories', 'weight_kg': 12,   'quantity': 4, 'status': 'good', 'description': 'Cast iron kettlebell'},
    {'name': 'Kettlebell 16 kg',               'category': 'accessories', 'weight_kg': 16,   'quantity': 4, 'status': 'good', 'description': 'Cast iron kettlebell'},
    {'name': 'Kettlebell 20 kg',               'category': 'accessories', 'weight_kg': 20,   'quantity': 4, 'status': 'good', 'description': 'Cast iron kettlebell'},
    {'name': 'Kettlebell 24 kg',               'category': 'accessories', 'weight_kg': 24,   'quantity': 2, 'status': 'good', 'description': 'Cast iron kettlebell'},
    {'name': 'Kettlebell 32 kg',               'category': 'accessories', 'weight_kg': 32,   'quantity': 2, 'status': 'good', 'description': 'Cast iron kettlebell'},
    {'name': 'Medicine Ball 3 kg',             'category': 'accessories', 'weight_kg': 3,    'quantity': 4, 'status': 'good', 'description': 'Rubber medicine ball'},
    {'name': 'Medicine Ball 5 kg',             'category': 'accessories', 'weight_kg': 5,    'quantity': 4, 'status': 'good', 'description': 'Rubber medicine ball'},
    {'name': 'Medicine Ball 8 kg',             'category': 'accessories', 'weight_kg': 8,    'quantity': 4, 'status': 'good', 'description': 'Rubber medicine ball'},
    {'name': 'Medicine Ball 10 kg',            'category': 'accessories', 'weight_kg': 10,   'quantity': 2, 'status': 'good', 'description': 'Rubber medicine ball'},
    {'name': 'Resistance Band Set (Light)',    'category': 'accessories', 'weight_kg': None, 'quantity': 10, 'status': 'good', 'description': 'Light resistance loop bands'},
    {'name': 'Resistance Band Set (Heavy)',    'category': 'accessories', 'weight_kg': None, 'quantity': 10, 'status': 'good', 'description': 'Heavy resistance loop bands'},
    {'name': 'Pull-up Assist Band Set',        'category': 'accessories', 'weight_kg': None, 'quantity': 6,  'status': 'good', 'description': 'Thick pull-up assistance bands'},
    {'name': 'Foam Roller',                    'category': 'accessories', 'weight_kg': None, 'quantity': 8,  'status': 'good', 'description': 'High-density foam roller'},
    {'name': 'Yoga Mat',                       'category': 'accessories', 'weight_kg': None, 'quantity': 20, 'status': 'good', 'description': 'Non-slip exercise mat'},
    {'name': 'Jump Rope',                      'category': 'accessories', 'weight_kg': None, 'quantity': 10, 'status': 'good', 'description': 'Speed jump rope'},
    {'name': 'Ab Wheel',                       'category': 'accessories', 'weight_kg': None, 'quantity': 6,  'status': 'good', 'description': 'Ab roller wheel'},
    {'name': 'Dip Belt',                       'category': 'accessories', 'weight_kg': None, 'quantity': 4,  'status': 'good', 'description': 'Leather dip/pull-up weight belt'},
    {'name': 'Lifting Belt',                   'category': 'accessories', 'weight_kg': None, 'quantity': 6,  'status': 'good', 'description': '4-inch leather powerlifting belt'},
    {'name': 'Wrist Wraps',                    'category': 'accessories', 'weight_kg': None, 'quantity': 8,  'status': 'good', 'description': 'Wrist support wraps'},
    {'name': 'Knee Sleeves',                   'category': 'accessories', 'weight_kg': None, 'quantity': 8,  'status': 'good', 'description': 'Neoprene knee sleeves'},
    {'name': 'Barbell Collars (Spring)',       'category': 'accessories', 'weight_kg': None, 'quantity': 20, 'status': 'good', 'description': 'Spring clip barbell collars'},
    {'name': 'Barbell Collars (Lock-jaw)',     'category': 'accessories', 'weight_kg': None, 'quantity': 12, 'status': 'good', 'description': 'Lock-jaw Olympic collars'},
    {'name': 'Weight Storage Tree',            'category': 'accessories', 'weight_kg': None, 'quantity': 6,  'status': 'good', 'description': 'Olympic plate storage tree'},
    {'name': 'Dumbbell Rack (3-tier)',         'category': 'accessories', 'weight_kg': None, 'quantity': 4,  'status': 'good', 'description': '3-tier dumbbell storage rack'},
    {'name': 'Mirror Panel (Wall)',            'category': 'accessories', 'weight_kg': None, 'quantity': 12, 'status': 'good', 'description': 'Full-length wall mirror panel'},
    {'name': 'Rubber Flooring Mat (1m²)',      'category': 'accessories', 'weight_kg': None, 'quantity': 80, 'status': 'good', 'description': 'Interlocking rubber gym floor tile'},
]


def seed_equipment(apps, schema_editor):
    InventoryItem = apps.get_model('inventory', 'InventoryItem')
    for item in EQUIPMENT:
        InventoryItem.objects.create(**item)


def unseed_equipment(apps, schema_editor):
    InventoryItem = apps.get_model('inventory', 'InventoryItem')
    InventoryItem.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_equipment, unseed_equipment),
    ]
