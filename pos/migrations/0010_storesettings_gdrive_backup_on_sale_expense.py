from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0009_storesettings_gdrive_credentials_json_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='storesettings',
            name='gdrive_backup_on_sale',
            field=models.BooleanField(
                default=False,
                help_text='Automatically upload a backup record to Google Drive whenever a sale is completed'
            ),
        ),
        migrations.AddField(
            model_name='storesettings',
            name='gdrive_backup_on_expense',
            field=models.BooleanField(
                default=False,
                help_text='Automatically upload a backup record to Google Drive whenever an expense is added'
            ),
        ),
    ]
