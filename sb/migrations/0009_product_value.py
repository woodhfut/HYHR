# Generated by Django 2.0.6 on 2018-08-29 08:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sb', '0008_auto_20180829_1436'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='value',
            field=models.PositiveSmallIntegerField(default=1),
        ),
    ]
