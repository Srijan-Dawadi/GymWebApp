from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='approval_status',
            field=models.CharField(
                choices=[('pending', 'Pending Review'), ('approved', 'Approved'), ('flagged', 'Flagged')],
                default='pending',
                db_index=True,
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='payment',
            name='reviewed_by',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='reviewed_payments',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='payment',
            name='reviewed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='payment',
            name='flag_reason',
            field=models.TextField(blank=True),
        ),
    ]
