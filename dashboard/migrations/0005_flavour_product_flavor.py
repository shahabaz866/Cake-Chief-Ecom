# Generated by Django 5.1.1 on 2024-10-17 10:02

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0004_category_product_category'),
    ]

    operations = [
        migrations.CreateModel(
            name='Flavour',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(max_length=250)),
            ],
        ),
        migrations.AddField(
            model_name='product',
            name='flavor',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='flsvours', to='dashboard.flavour'),
        ),
    ]
