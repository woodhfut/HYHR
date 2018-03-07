from django.db import models
from django.contrib.auth.admin import User
from django.utils import timezone

# Create your models here.
class User_extra_info(models.Model):
    username = models.CharField(max_length=100, null=False, unique=True)
    pid = models.CharField(max_length=18, unique=True, null=False)
    realname = models.CharField(max_length=50, null=False)
    phone = models.CharField(max_length=11, null=False)
    comment = models.CharField(max_length=200, null=True)

    def __str__(self):
        return 'name: ' + self.username + '(' + self.realname + ' pid: ' + self.pid + ' phoneNo: ' + self.phone + ')'

class Partner(models.Model):
    name = models.CharField(max_length = 30)
    phone = models.CharField(max_length = 120, null=True, blank =True)
    im = models.CharField(max_length = 120, null=True, blank =True)
    note =  models.CharField(max_length = 120, null=True, blank =True)

    def __str__(self):
        return self.name


class Customer(models.Model):
    name = models.CharField(max_length = 30)
    pid = models.CharField(max_length=18, unique=True)
    phone = models.CharField(max_length = 120) #; seperated, could save 10 cell phone numbers
    Hukou_Type = (
        ('C','城市'),
        ('N','农村'),
        )

    hukou = models.CharField(max_length = 8, choices=Hukou_Type)
    
    wechat = models.CharField(max_length = 50, null= True, blank=True)   
    introducer = models.CharField(max_length = 30, null=True, blank=True)
    note = models.CharField(max_length = 50, null= True, blank=True)
    
    def __str__(self):
        return self.name + '(' + self.pid + ')'

class Product(models.Model):
    name = models.CharField(max_length = 30)
    lowest_baseline = models.FloatField()
    customers = models.ManyToManyField(Customer, through='Product_Order')
    validFrom = models.DateField()
    validTo = models.DateField()
    note = models.CharField(max_length = 50, null= True, blank=True)
    def __str__(self):
        return self.name

class Service_Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete = models.CASCADE)
    svalidFrom = models.DateField()
    svalidTo = models.DateField()
    stotal_price = models.FloatField() 
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE)
    sprice2Partner = models.FloatField() 
    pay_method=(
        ('WX','微信'),
        ('ZFB','支付宝'),
        ('YHK','银行卡'),
        )
    paymethod = models.CharField(max_length =3 , choices=pay_method)
    payaccount = models.CharField(max_length = 30)
    
    orderDate = models.DateField(default=timezone.now())
    dealPlatform = models.CharField(max_length = 10, null=True, blank=True)
    snote = models.CharField(max_length = 100, null=True, blank=True)

    def __str__(self):
        return self.customer.name + '(' + self.product.name + ':' + self.validFrom.strftime('%Y/%m/%d') + '--' + self.validTo.strftime('%Y/%m/%d') + ')'

class Product_Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete = models.CASCADE)
    district_options = (
        ('BJCY','朝阳'),
        ('BJHD','海淀'),
        ('BJDC','东城'),
        ('BJXC','西城'),
        ('BJFT','丰台'),
        ('BJDX','大兴'),
        ('BJTZ','通州'),
        ('BJCP','昌平'),
        ('BJHR','怀柔'),
        ('BJPG','平谷'),
        ('BJYQ','延庆'),
        )
    district = models.CharField(max_length = 5, choices=district_options, default='BJFT')
    product_base = models.FloatField()
    validFrom = models.DateField()
    validTo = models.DateField()
    total_price = models.FloatField()
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE)
    price2Partner = models.FloatField() 
    pay_method=(
        ('WX','微信'),
        ('ZFB','支付宝'),
        ('YHK','银行卡'),
        )
    paymethod = models.CharField(max_length =3 , choices=pay_method)
    payaccount = models.CharField(max_length = 30)
    
    orderDate = models.DateField(default=timezone.now())
    dealPlatform = models.CharField(max_length = 10, null=True, blank=True)
    note = models.CharField(max_length = 100, null=True, blank=True)

    def __str__(self):
        return self.customer.name + '(' + self.product.name + ':' + self.validFrom.strftime('%Y/%m/%d') + '--' + self.validTo.strftime('%Y/%m/%d') + ')'