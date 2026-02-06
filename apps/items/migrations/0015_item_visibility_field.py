# Generated manually for item visibility changes

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('items', '0014_merge_20260105_2109'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='is_public',
            field=models.CharField(choices=[('public', 'Public'), ('private', 'Private'), ('restricted', 'Restricted')], default='public', help_text='Public: visible to everyone, Private: hidden, Restricted: only group members', max_length=10, verbose_name='visibility'),
        ),
        migrations.RenameField(
            model_name='item',
            old_name='is_public',
            new_name='visibility',
        ),
    ]