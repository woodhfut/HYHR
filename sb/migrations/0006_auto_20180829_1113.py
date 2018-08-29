# Generated by Django 2.0.6 on 2018-08-29 03:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sb', '0005_auto_20180828_1936'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomerStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20)),
                ('value', models.PositiveSmallIntegerField()),
            ],
        ),
        migrations.AlterField(
            model_name='customer',
            name='status',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, to='sb.CustomerStatus'),
        ),
        migrations.AlterField(
            model_name='product_order',
            name='orderDate',
            field=models.DateField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='service_order',
            name='orderDate',
            field=models.DateField(auto_now=True),
        ),
    ]
