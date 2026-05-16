from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0002_add_address_to_member'),
    ]

    operations = [
        migrations.AddField(
            model_name='member',
            name='is_flagged',
            field=models.BooleanField(
                default=False,
                help_text='Flagged members are blocked from face recognition attendance.',
            ),
        ),
    ]
