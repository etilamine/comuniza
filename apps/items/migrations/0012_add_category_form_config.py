# Generated manually for adding form configuration fields to ItemCategory

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('items', '0011_fix_empty_identifiers'),
    ]

    operations = [
        migrations.AddField(
            model_name='itemcategory',
            name='form_field_help',
            field=models.JSONField(blank=True, default=dict, help_text='JSON object mapping field names to custom help text for this category', verbose_name='field help text'),
        ),
        migrations.AddField(
            model_name='itemcategory',
            name='form_field_labels',
            field=models.JSONField(blank=True, default=dict, help_text='JSON object mapping field names to custom labels for this category', verbose_name='field labels'),
        ),
        migrations.AddField(
            model_name='itemcategory',
            name='form_hidden_fields',
            field=models.JSONField(blank=True, default=list, help_text='JSON list of field names that should be hidden for this category', verbose_name='hidden fields'),
        ),
        migrations.AddField(
            model_name='itemcategory',
            name='form_optional_fields',
            field=models.JSONField(blank=True, default=list, help_text='JSON list of field names that should be optional for this category', verbose_name='optional fields'),
        ),
        migrations.AddField(
            model_name='itemcategory',
            name='form_required_fields',
            field=models.JSONField(blank=True, default=list, help_text='JSON list of field names that should be required for this category', verbose_name='required fields'),
        ),
    ]