# Generated manually for populating form_field_order with defaults

from django.db import migrations


def populate_form_field_order(apps, schema_editor):
    """Populate existing categories with default field ordering."""
    ItemCategory = apps.get_model('items', 'ItemCategory')

    # Default field order for all categories
    default_field_order = [
        "title",
        "description",
        "category",
        "author",
        "publisher",
        "languages",
        "book_format",
        "subjects",
        "isbn",
        "year",
        "condition",
        "status",
        "estimated_value",
        "max_loan_days",
        "groups",
        "is_public",
        "allow_reservations"
    ]

    # Update all existing categories with the default field order
    ItemCategory.objects.filter(is_active=True).update(
        form_field_order=default_field_order
    )


def reverse_populate_form_field_order(apps, schema_editor):
    """Reverse migration: clear form_field_order."""
    ItemCategory = apps.get_model('items', 'ItemCategory')
    ItemCategory.objects.update(form_field_order=[])


class Migration(migrations.Migration):

    dependencies = [
        ('items', '0003_add_category_form_field_order'),  # The migration that adds the field
    ]

    operations = [
        migrations.RunPython(
            populate_form_field_order,
            reverse_code=reverse_populate_form_field_order
        ),
    ]