# Generated migration for User model to use easy-thumbnails

from django.db import migrations, models
import easy_thumbnails.fields


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_alter_user_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='avatar',
            field=easy_thumbnails.fields.ThumbnailerImageField(
                upload_to='avatars/',
                blank=True,
                null=True,
                resize_source=dict(size=(180, 180), quality=90)
            ),
            preserve_default=False,
        ),
    ]
