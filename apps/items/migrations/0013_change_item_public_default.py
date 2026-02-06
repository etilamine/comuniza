# Change Item.is_public default to True

from django.db import migrations, models
import django.utils.translation


class Migration(migrations.Migration):

    dependencies = [
        ('items', '0012_add_category_form_config'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='is_public',
            field=models.BooleanField(
                default=True,
                help_text='Make this item visible to all users, not just group members',
                verbose_name='public visibility'
            ),
        ),
    ]