# Generated by Django 2.0.6 on 2018-08-27 07:12

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('sb', '0002_auto_20180825_2254'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product_order',
            name='partner',
        ),
        migrations.RemoveField(
            model_name='product_order',
            name='price2Partner',
        ),
        migrations.AlterField(
            model_name='product_order',
            name='orderDate',
            field=models.DateField(default=datetime.datetime(2018, 8, 27, 7, 12, 0, 419731, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='service_order',
            name='orderDate',
            field=models.DateField(default=datetime.datetime(2018, 8, 27, 7, 12, 0, 416739, tzinfo=utc)),
        ),
    ]
