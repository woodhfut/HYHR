# Generated by Django 2.1 on 2018-09-02 09:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sb', '0012_operations'),
    ]

    operations = [
        migrations.AlterField(
            model_name='operations',
            name='oper_date',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='product_order',
            name='orderDate',
            field=models.DateField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='service_order',
            name='orderDate',
            field=models.DateField(auto_now_add=True),
        ),
    ]
