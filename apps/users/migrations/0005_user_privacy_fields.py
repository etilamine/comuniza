# Generated manually for user privacy settings

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_hash_existing_emails'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='default_item_visibility',
            field=models.CharField(choices=[('public', 'Public'), ('private', 'Private'), ('restricted', 'Restricted')], default='public', help_text='Default visibility for new items', max_length=10, verbose_name='default item visibility'),
        ),
        migrations.AddField(
            model_name='user',
            name='groups_visibility',
            field=models.CharField(choices=[('private', 'Private - Only group members'), ('public', 'Public - Anyone can view'), ('lenders_borrowers', 'Lenders/Borrowers - Only users you\'ve transacted with in that group')], default='private', help_text='Who can see your groups', max_length=20, verbose_name='groups visibility'),
        ),
        migrations.AddField(
            model_name='user',
            name='location_visibility',
            field=models.CharField(choices=[('private', 'Private - Only group members'), ('public', 'Public - Anyone can view'), ('lenders_borrowers', 'Lenders/Borrowers - Only users you\'ve transacted with')], default='private', help_text='Who can see your location', max_length=20, verbose_name='location visibility'),
        ),
        migrations.AlterField(
            model_name='user',
            name='profile_visibility',
            field=models.CharField(choices=[('private', 'Private - Only group members'), ('public', 'Public - Anyone can view'), ('lenders_borrowers', 'Lenders/Borrowers - Only users you\'ve transacted with')], default='private', help_text='Who can see your profile information', max_length=20, verbose_name='profile visibility'),
        ),
    ]