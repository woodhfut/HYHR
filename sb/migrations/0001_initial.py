# Generated by Django 3.0.4 on 2020-04-27 16:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('pid', models.CharField(max_length=18)),
                ('phone', models.CharField(max_length=11)),
                ('hukou', models.CharField(choices=[('C', '城市'), ('N', '农村')], max_length=8)),
                ('status', models.PositiveSmallIntegerField(default=0)),
                ('wechat', models.CharField(blank=True, max_length=50, null=True)),
                ('introducer', models.CharField(blank=True, max_length=30, null=True)),
                ('note', models.TextField(blank=True, max_length=50, null=True)),
            ],
            options={
                'verbose_name': '客户',
                'verbose_name_plural': '客户',
            },
        ),
        migrations.CreateModel(
            name='District',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
            ],
            options={
                'verbose_name': '所属区县',
                'verbose_name_plural': '所属区县',
            },
        ),
        migrations.CreateModel(
            name='OrderType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20)),
            ],
            options={
                'verbose_name': '订单类型',
                'verbose_name_plural': '订单类型',
            },
        ),
        migrations.CreateModel(
            name='Partner',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('phone', models.CharField(blank=True, max_length=120, null=True)),
                ('im', models.CharField(blank=True, max_length=120, null=True)),
                ('note', models.TextField(blank=True, max_length=120, null=True)),
            ],
            options={
                'verbose_name': '合作伙伴',
                'verbose_name_plural': '合作伙伴',
            },
        ),
        migrations.CreateModel(
            name='PayMethod',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20)),
            ],
            options={
                'verbose_name': '支付方法',
                'verbose_name_plural': '支付方法',
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('code', models.PositiveSmallIntegerField(default=1)),
                ('lowest_baseline', models.FloatField()),
                ('validFrom', models.DateField()),
                ('validTo', models.DateField()),
                ('note', models.TextField(blank=True, max_length=50, null=True)),
            ],
            options={
                'verbose_name': '产品',
                'verbose_name_plural': '产品',
            },
        ),
        migrations.CreateModel(
            name='TodoList',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('info', models.TextField(max_length=500, verbose_name='待办事宜')),
                ('isfinished', models.BooleanField(default=False, verbose_name='是否已完成')),
            ],
            options={
                'verbose_name': '待办事宜',
                'verbose_name_plural': '待办事宜',
            },
        ),
        migrations.CreateModel(
            name='User_extra_info',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=100, unique=True)),
                ('pid', models.CharField(max_length=18, unique=True)),
                ('realname', models.CharField(max_length=50)),
                ('phone', models.CharField(max_length=11)),
                ('comment', models.TextField(max_length=200, null=True)),
            ],
            options={
                'verbose_name': '补充用户信息',
                'verbose_name_plural': '补充用户信息',
            },
        ),
        migrations.CreateModel(
            name='Service_Order',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('svalidFrom', models.DateField()),
                ('svalidTo', models.DateField()),
                ('stotal_price', models.FloatField()),
                ('payaccount', models.CharField(max_length=30)),
                ('orderDate', models.DateField(auto_now_add=True)),
                ('sprice2Partner', models.FloatField(blank=True, default=0, null=True)),
                ('snote', models.TextField(blank=True, max_length=100, null=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sb.Customer')),
                ('partner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='sb.Partner')),
                ('paymethod', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sb.PayMethod')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sb.Product')),
            ],
            options={
                'verbose_name': '服务费订单',
                'verbose_name_plural': '服务费订单',
            },
        ),
        migrations.CreateModel(
            name='Product_Order',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_base', models.FloatField()),
                ('validFrom', models.DateField()),
                ('validTo', models.DateField()),
                ('total_price', models.FloatField()),
                ('payaccount', models.CharField(max_length=30)),
                ('orderDate', models.DateField(auto_now_add=True)),
                ('note', models.TextField(blank=True, max_length=100, null=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sb.Customer')),
                ('district', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='sb.District')),
                ('orderType', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='sb.OrderType')),
                ('paymethod', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sb.PayMethod')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sb.Product')),
            ],
            options={
                'verbose_name': '产品订单',
                'verbose_name_plural': '产品订单',
            },
        ),
        migrations.AddField(
            model_name='product',
            name='customers',
            field=models.ManyToManyField(through='sb.Product_Order', to='sb.Customer'),
        ),
        migrations.CreateModel(
            name='Operations',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('oper_date', models.DateTimeField(auto_now_add=True)),
                ('operation', models.PositiveSmallIntegerField(choices=[(1, '新增'), (2, '续费'), (3, '减员')])),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sb.Customer')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sb.Product')),
            ],
            options={
                'verbose_name': '操作',
                'verbose_name_plural': '操作',
            },
        ),
    ]
