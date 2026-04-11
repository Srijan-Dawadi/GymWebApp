from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='MembershipPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('price', models.DecimalField(decimal_places=2, max_digits=8)),
                ('duration_days', models.PositiveIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Member',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=200)),
                ('phone', models.CharField(max_length=20)),
                ('email', models.EmailField(unique=True)),
                ('photo', models.ImageField(blank=True, null=True, upload_to='member_photos/')),
                ('face_descriptor', models.JSONField(blank=True, null=True)),
                ('join_date', models.DateField()),
                ('expiry_date', models.DateField()),
                ('status', models.CharField(choices=[('active', 'Active'), ('expired', 'Expired'), ('suspended', 'Suspended')], default='active', max_length=10)),
                ('membership_plan', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='members', to='members.membershipplan')),
            ],
        ),
    ]
