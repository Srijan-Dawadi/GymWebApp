from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='InventoryItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('category', models.CharField(
                    choices=[
                        ('dumbbells', 'Dumbbells'),
                        ('barbells', 'Barbells & Bars'),
                        ('weight_plates', 'Weight Plates'),
                        ('cardio', 'Cardio Machines'),
                        ('strength', 'Strength Machines'),
                        ('accessories', 'Accessories'),
                    ],
                    default='accessories',
                    max_length=50,
                )),
                ('description', models.TextField(blank=True)),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('status', models.CharField(
                    choices=[
                        ('good', 'Good'),
                        ('maintenance', 'Needs Maintenance'),
                        ('out_of_service', 'Out of Service'),
                    ],
                    default='good',
                    max_length=20,
                )),
                ('weight_kg', models.FloatField(blank=True, help_text='Weight in kg (for dumbbells/plates/bars)', null=True)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['category', 'weight_kg', 'name'],
            },
        ),
    ]
