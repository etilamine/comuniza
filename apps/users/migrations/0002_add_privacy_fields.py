# Generated manually for privacy fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='username',
            field=models.CharField(blank=True, help_text='Public identifier (Reddit-style generated)', max_length=50, unique=True, verbose_name='username'),
        ),
        migrations.AddField(
            model_name='user',
            name='email_hash',
            field=models.CharField(blank=True, help_text='SHA-256 hash of email for privacy', max_length=200, verbose_name='email hash'),
        ),
        migrations.AddField(
            model_name='user',
            name='phone_hash',
            field=models.CharField(blank=True, help_text='SHA-256 hash of phone for privacy', max_length=200, verbose_name='phone hash'),
        ),
        migrations.AddField(
            model_name='user',
            name='profile_visibility',
            field=models.CharField(choices=[('private', 'Private - Only group members'), ('public', 'Public - Anyone can view')], default='private', help_text='Who can see your profile information', max_length=20, verbose_name='profile visibility'),
        ),
        migrations.AddField(
            model_name='user',
            name='email_visibility',
            field=models.CharField(choices=[('private', 'Private - Never shown'), ('members', 'Group members only'), ('public', 'Public - Everyone')], default='private', help_text='Who can see your email address', max_length=20, verbose_name='email visibility'),
        ),
        migrations.AddField(
            model_name='user',
            name='activity_visibility',
            field=models.CharField(choices=[('private', 'Private - No activity shown'), ('limited', 'Limited - Basic stats only'), ('public', 'Public - Full activity')], default='private', help_text='How much of your sharing activity is visible', max_length=20, verbose_name='activity visibility'),
        ),
        migrations.AddField(
            model_name='user',
            name='last_password_change',
            field=models.DateTimeField(blank=True, null=True, verbose_name='last password change'),
        ),
        migrations.AddField(
            model_name='user',
            name='password_reset_required',
            field=models.BooleanField(default=False, verbose_name='password reset required'),
        ),
    ]