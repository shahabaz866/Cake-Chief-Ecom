# Generated by Django 5.1.1 on 2024-11-21 07:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cart_app', '0010_cartitem_price_alter_cartitem_variant'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cartitem',
            name='total_price',
        ),
    ]