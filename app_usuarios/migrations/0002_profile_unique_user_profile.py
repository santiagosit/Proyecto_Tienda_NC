# Generated by Django 5.1.1 on 2025-03-31 05:07

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_usuarios', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='profile',
            constraint=models.UniqueConstraint(fields=('user',), name='unique_user_profile'),
        ),
    ]
