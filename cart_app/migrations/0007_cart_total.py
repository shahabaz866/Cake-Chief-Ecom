# Generated by Django 5.1.1 on 2024-11-02 11:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cart_app', '0006_order_orderitem'),
    ]

    operations = [
        migrations.AddField(
            model_name='cart',
            name='total',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
    ]