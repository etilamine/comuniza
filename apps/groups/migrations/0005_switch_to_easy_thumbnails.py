# Generated migration for Group model to use easy-thumbnails

from django.db import migrations, models
import easy_thumbnails.fields


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0004_alter_group_members'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='image',
            field=easy_thumbnails.fields.ThumbnailerImageField(
                upload_to='groups/',
                blank=True,
                null=True,
                resize_source=dict(size=(1000, 300), quality=90)
            ),
            preserve_default=False,
        ),
    ]
