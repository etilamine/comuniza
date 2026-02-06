# Generated migration for GDPR-compliant email hashing

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_add_privacy_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='created at'),
        ),
        migrations.AddField(
            model_name='user',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='updated at'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['email_hash'], name='users_user_email_h_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['username'], name='users_user_userna_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['-created_at'], name='users_user_created_idx'),
        ),
        migrations.RunPython(
            code=migrations.RunPython.noop,
            reverse_code=migrations.RunPython.noop,
        ),
    ]