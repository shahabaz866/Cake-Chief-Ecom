# Generated by Django 5.1.1 on 2024-10-22 12:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0009_productimages'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='cropped_image',
            field=models.ImageField(blank=True, null=True, upload_to='products/cropped_images/'),
        ),
    ]
