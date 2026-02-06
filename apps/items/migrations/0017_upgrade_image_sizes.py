# Generated migration for image size upgrades

from django.db import migrations, models
import easy_thumbnails.fields


class Migration(migrations.Migration):

    dependencies = [
        ('items', '0016_switch_to_easy_thumbnails'),
    ]

    operations = [
        migrations.AlterField(
            model_name='itemimage',
            name='image',
            field=easy_thumbnails.fields.ThumbnailerImageField(
                resize_source={'size': (2000, 2000), 'quality': 90},
                upload_to='items/',
                verbose_name='image'
            ),
        ),
    ]