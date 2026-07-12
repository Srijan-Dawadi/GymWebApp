from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('members', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('check_in_time', models.TimeField(auto_now_add=True)),
                ('date', models.DateField(auto_now_add=True)),
                ('method', models.CharField(choices=[('face', 'Face'), ('manual', 'Manual')], max_length=10)),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendances', to='members.member')),
            ],
            options={
                'ordering': ['-date', '-check_in_time'],
                'unique_together': {('member', 'date')},
            },
        ),
    ]
