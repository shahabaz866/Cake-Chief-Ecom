# Generated by Django 5.1.1 on 2024-11-01 04:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cart_app', '0002_remove_cart_items_remove_cart_updated_at_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='cartitem',
            name='total_price',
            field=models.IntegerField(default=0),
        ),
    ]