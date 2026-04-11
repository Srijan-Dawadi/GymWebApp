from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('members', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=8)),
                ('date_paid', models.DateField()),
                ('period_start', models.DateField()),
                ('period_end', models.DateField()),
                ('payment_method', models.CharField(choices=[('cash', 'Cash'), ('card', 'Card'), ('transfer', 'Transfer')], max_length=20)),
                ('notes', models.TextField(blank=True)),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='members.member')),
            ],
        ),
    ]
