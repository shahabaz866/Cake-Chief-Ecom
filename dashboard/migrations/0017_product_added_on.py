# Generated by Django 5.1.1 on 2024-11-02 13:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0016_alter_size_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='added_on',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]