# Generated by Django 5.1.1 on 2024-10-29 09:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0013_size_product_sizes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='sizes',
            field=models.ManyToManyField(related_name='products', to='dashboard.size'),
        ),
    ]
