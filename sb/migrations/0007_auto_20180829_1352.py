# Generated by Django 2.0.6 on 2018-08-29 05:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sb', '0006_auto_20180829_1113'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='pid',
            field=models.CharField(max_length=18),
        ),
    ]