# Generated by Django 5.1.1 on 2024-10-08 12:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0003_remove_customuser_username_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='CustomUser',
        ),
    ]
