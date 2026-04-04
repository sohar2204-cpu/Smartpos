from django.db import migrations, models


class Migration(migrations.Migration):
    """
    SEC-PIN Migration: Replace plaintext `pin` field with `pin_hash` field.
    
    This migration:
    1. Adds the new `pin_hash` field
    2. Clears all existing plaintext PINs (they cannot be safely migrated
       because we need the original plain value to hash it — existing users
       will simply need a PIN reset from an admin)
    3. Removes the old `pin` field
    """

    dependencies = [
        ('pos', '0016_category_created_at'),
    ]

    operations = [
        # Step 1: Add the new hashed PIN field
        migrations.AddField(
            model_name='userprofile',
            name='pin_hash',
            field=models.CharField(
                max_length=128,
                blank=True,
                default='',
                help_text='Salted hash of the 4-digit PIN. Never store raw PINs.',
            ),
        ),
        # Step 2: Remove the old plaintext PIN field
        # Note: existing PINs are intentionally NOT migrated.
        # Admins must re-set PINs via the manage_pins page after this migration.
        migrations.RemoveField(
            model_name='userprofile',
            name='pin',
        ),
    ]
