# Fix items with empty identifiers
from django.db import migrations
import random
import string


def fix_empty_identifiers(apps, schema_editor):
    Item = apps.get_model('items', 'Item')

    # Find items with empty identifiers
    empty_items = Item.objects.filter(identifier='')

    for item in empty_items:
        # Generate a new 10-character alphanumeric identifier
        chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

        # Ensure uniqueness
        while Item.objects.filter(identifier=chars).exists():
            chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

        item.identifier = chars
        item.save()


class Migration(migrations.Migration):

    dependencies = [
        ('items', '0010_convert_to_10char_identifiers'),
    ]

    operations = [
        migrations.RunPython(fix_empty_identifiers),
    ]