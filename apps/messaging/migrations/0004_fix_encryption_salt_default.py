from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ("messaging", "0002_conversation_related_item_conversation_related_loan"),
    ]

    operations = [
        migrations.AlterField(
            model_name='conversation',
            name='encryption_salt',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Salt used for end-to-end encryption key derivation',
                max_length=100,
                verbose_name='encryption salt'
            ),
        ),
    ]
