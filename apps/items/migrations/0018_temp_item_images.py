# Generated manually for TempItemImage model

from django.db import migrations, models
import django.db.models.deletion
import easy_thumbnails.fields


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_switch_to_easy_thumbnails'),
        ('items', '0017_upgrade_image_sizes'),
    ]

    operations = [
        migrations.CreateModel(
            name='TempItemImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_key', models.CharField(blank=True, db_index=True, default='', max_length=40, verbose_name='session key')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True, verbose_name='uploaded at')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='order')),
                ('image', easy_thumbnails.fields.ThumbnailerImageField(
                    upload_to='temp_items/', 
                    verbose_name='image',
                    resize_source=dict(size=(2000, 2000), quality=90)
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE, 
                    to='users.user', 
                    verbose_name='user'
                )),
            ],
            options={
                'verbose_name': 'temporary item image',
                'verbose_name_plural': 'temporary item images',
                'db_table': 'temp_item_images',
                'ordering': ['order', 'uploaded_at'],
                'indexes': [
                    models.Index(fields=['user', 'session_key'], name='items_tempim_user_session_key_idx'),
                    models.Index(fields=['uploaded_at'], name='items_tempim_uploaded_at_idx'),
                ],
            },
        ),
    ]