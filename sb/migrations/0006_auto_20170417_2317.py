# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-04-18 06:17
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('sb', '0005_user_extra_info'),
    ]

    operations = [
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('pid', models.CharField(max_length=18, unique=True)),
                ('phone', models.CharField(max_length=120)),
                ('hukou', models.CharField(choices=[('C', '城市'), ('N', '农村')], max_length=8)),
                ('district', models.CharField(choices=[('CY', '朝阳'), ('HD', '海淀'), ('DC', '东城'), ('XC', '西城'), ('FT', '丰台'), ('DX', '大兴'), ('TZ', '通州'), ('CP', '昌平'), ('HR', '怀柔'), ('PG', '平谷'), ('YQ', '延庆')], default='FT', max_length=2)),
                ('wechat', models.CharField(blank=True, max_length=50, null=True)),
                ('introducer', models.CharField(blank=True, max_length=30, null=True)),
                ('note', models.CharField(blank=True, max_length=50, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('validFrom', models.DateField()),
                ('validTo', models.DateField()),
                ('product_base', models.FloatField()),
                ('total_price', models.FloatField()),
                ('paymethod', models.CharField(choices=[('WX', '微信'), ('ZFB', '支付宝'), ('YHK', '银行卡')], max_length=3)),
                ('payaccount', models.CharField(max_length=30)),
                ('orderDate', models.DateField(default=datetime.datetime(2017, 4, 18, 6, 17, 46, 981352, tzinfo=utc))),
                ('dealPlatform', models.CharField(blank=True, max_length=10, null=True)),
                ('note', models.CharField(blank=True, max_length=100, null=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sb.Customer')),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('baseline', models.FloatField()),
                ('validFrom', models.DateField()),
                ('validTo', models.DateField()),
                ('price', models.FloatField()),
                ('note', models.CharField(blank=True, max_length=50, null=True)),
                ('customers', models.ManyToManyField(through='sb.Order', to='sb.Customer')),
            ],
        ),
        migrations.AddField(
            model_name='order',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sb.Product'),
        ),
    ]
