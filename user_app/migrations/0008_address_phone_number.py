# Generated by Django 5.1.1 on 2024-11-12 14:36

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_app', '0007_alter_usercontact_unique_together_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='address',
            name='phone_number',
            field=models.CharField(max_length=10, null=True, validators=[django.core.validators.RegexValidator('^\\d{10}$', message='Phone number must be 10 digits.')]),
        ),
    ]
