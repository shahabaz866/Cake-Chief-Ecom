# Generated by Django 5.1.1 on 2024-11-11 14:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order_app', '0005_alter_order_order_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='order_status',
            field=models.CharField(choices=[('PENDING', 'Pending'), ('PROCESSING', 'Processing'), ('SHIPPED', 'Shipped'), ('DELIVERED', 'Delivered'), ('CANCELLED', 'Cancelled'), ('REFUND', 'Refund'), ('DISPATCH', 'Dispatch')], default='Pending', max_length=20),
        ),
    ]
