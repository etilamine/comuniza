# Data migration to hash existing emails for GDPR compliance

from django.db import migrations
from apps.users.utils.privacy import hash_email


def hash_existing_emails(apps, schema_editor):
    """Hash all existing emails in the database."""
    User = apps.get_model('users', 'User')
    
    users_to_update = User.objects.filter(email__isnull=False, email_hash='')
    
    for user in users_to_update:
        if user.email:
            user.email_hash = hash_email(user.email)
            user.save(update_fields=['email_hash'])


def reverse_hash_emails(apps, schema_editor):
    """Clear email hashes (reversible operation)."""
    User = apps.get_model('users', 'User')
    User.objects.all().update(email_hash='')


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_email_hashing_gdpr'),
    ]

    operations = [
        migrations.RunPython(hash_existing_emails, reverse_hash_emails),
    ]