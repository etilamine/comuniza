# Generated migration for switching to easy-thumbnails

from django.db import migrations, models
import easy_thumbnails.fields


class Migration(migrations.Migration):

    dependencies = [
        ('items', '0015_item_visibility_field'),
    ]

    operations = [
        # This migration is for switching from ImageField to ThumbnailerImageField
        # The field type change is handled automatically by Django
        migrations.AlterField(
            model_name='itemimage',
            name='image',
            field=easy_thumbnails.fields.ThumbnailerImageField(
                upload_to='items/',
                resize_source=dict(size=(1200, 900), quality=90)
            ),
            preserve_default=False,
        ),
    ]
