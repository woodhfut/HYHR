# Generated by Django 3.0.4 on 2020-04-28 02:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sb', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product_order',
            name='paymethod',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='service_order',
            name='paymethod',
            field=models.CharField(max_length=100),
        ),
    ]
