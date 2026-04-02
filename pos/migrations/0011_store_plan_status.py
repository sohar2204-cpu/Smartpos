from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0010_storesettings_gdrive_backup_on_sale_expense'),
    ]

    operations = [
        migrations.AddField(
            model_name='store',
            name='plan',
            field=models.CharField(
                max_length=20,
                default='starter',
                choices=[
                    ('starter',    'Starter (Free)'),
                    ('pro',        'Pro'),
                    ('enterprise', 'Enterprise'),
                ],
                help_text='Subscription plan for this store',
            ),
        ),
        migrations.AddField(
            model_name='store',
            name='status',
            field=models.CharField(
                max_length=20,
                default='active',
                choices=[
                    ('active',    'Active'),
                    ('trial',     'Trial'),
                    ('suspended', 'Suspended'),
                    ('inactive',  'Inactive'),
                ],
            ),
        ),
    ]
