# Generated migration for image size upgrades

from django.db import migrations, models
import easy_thumbnails.fields
from apps.core.validators import validate_group_image


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0005_switch_to_easy_thumbnails'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='image',
            field=easy_thumbnails.fields.ThumbnailerImageField(
                blank=True,
                null=True,
                resize_source={'size': (2000, 2000), 'quality': 90},
                upload_to='groups/',
                validators=[validate_group_image],
                verbose_name='group image'
            ),
        ),
    ]