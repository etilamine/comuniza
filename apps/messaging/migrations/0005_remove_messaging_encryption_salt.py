from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ("messaging", "0004_fix_encryption_salt_default"),  # Adjust to match your latest migration
    ]

    operations = [
        migrations.RemoveField(
            model_name='message',
            name='encryption_salt',
        ),
    ]
