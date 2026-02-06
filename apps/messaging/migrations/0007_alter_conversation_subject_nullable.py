# Generated migration to make subject field nullable

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('messaging', '0006_alter_conversation_encryption_salt'),
    ]

    operations = [
        migrations.AlterField(
            model_name='conversation',
            name='subject',
            field=models.CharField(
                blank=True,
                help_text='Optional conversation subject',
                max_length=200,
                null=True,
                verbose_name='subject'
            ),
        ),
    ]
