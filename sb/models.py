from django.db import models
from django.contrib.auth.admin import User
from django.utils import timezone

# Create your models here.
class User_extra_info(models.Model):
    username = models.CharField(max_length=100, null=False, unique=True)
    pid = models.CharField(max_length=18, unique=True, null=False)
    realname = models.CharField(max_length=50, null=False)
    phone = models.CharField(max_length=11, null=False)
    comment = models.TextField(max_length=200, null=True)

    def __str__(self):
        return 'name: ' + self.username + '(' + self.realname + ' pid: ' + self.pid + ' phoneNo: ' + self.phone + ')'

    class Meta:
        verbose_name = '补充用户信息'
        verbose_name_plural = verbose_name

class Partner(models.Model):
    name = models.CharField(max_length = 30)
    phone = models.CharField(max_length = 120, null=True, blank =True)
    im = models.CharField(max_length = 120, null=True, blank =True)
    note =  models.TextField(max_length = 120, null=True, blank =True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '合作伙伴'
        verbose_name_plural = verbose_name

# class CustomerStatus(models.Model):
#     name = models.CharField(max_length = 20)
#     value = models.PositiveSmallIntegerField()

#     def __str__(self):
#         return self.name + '(' + str(self.value) + ')'

class Customer(models.Model):
    name = models.CharField(max_length = 30,verbose_name='姓名')
    pid = models.CharField(max_length=18, verbose_name='身份证号')
    phone = models.CharField(max_length = 11, null=True, blank=True) #公司客户，找对接人.
    Hukou_Type = (
        ('C','城市'),
        ('N','农村'),
        )

    hukou = models.CharField(max_length = 8, choices=Hukou_Type, verbose_name='户口')
    status = models.PositiveSmallIntegerField(default=0,verbose_name='状态')
    wechat = models.CharField(max_length = 50, null= True, blank=True, verbose_name='微信')   
    introducer = models.CharField(max_length = 30, null=True, blank=True, verbose_name='介绍人')
    note = models.TextField(max_length = 50, null= True, blank=True, verbose_name='备注')
    
    def __str__(self):
        return self.name + '(' + self.pid + ')'
    
    class Meta:
        verbose_name ='客户'
        verbose_name_plural = verbose_name

class Product(models.Model):
    name = models.CharField(max_length = 30, verbose_name='名称')
    code = models.PositiveSmallIntegerField( default=1, verbose_name='代码')
    #lowest_baseline = models.FloatField()
    customers = models.ManyToManyField(Customer, through='Product_Order')
    #validFrom = models.DateField()
    #validTo = models.DateField()
    note = models.TextField(max_length = 50, null= True, blank=True,verbose_name='备注')
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = '产品'
        verbose_name_plural = verbose_name


class PayMethod(models.Model):
    name = models.CharField(max_length = 20, verbose_name = '支付方法')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '支付方法'
        verbose_name_plural = verbose_name

class Service(models.Model):
    name = models.CharField(max_length = 30, verbose_name='名称')
    code = models.PositiveSmallIntegerField( default=1, verbose_name='代码')
    customers = models.ManyToManyField(Customer, through='Service_Order')
    note = models.TextField(max_length = 50, null= True, blank=True,verbose_name='备注')
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = '服务'
        verbose_name_plural = verbose_name

class Service_Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name='客户姓名')
    service = models.ForeignKey(Service, on_delete = models.CASCADE, verbose_name='服务名称', default=1)
    svalidFrom = models.DateField(verbose_name='起始日期')
    svalidTo = models.DateField(verbose_name='截至日期')
    stotal_price = models.FloatField(verbose_name='服务费')  

    paymethod =  models.CharField(max_length = 100, verbose_name='支付方式')
    
    orderDate = models.DateField(auto_now_add=True, verbose_name='支付日期')
    
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE,null=True, blank=True, verbose_name='合作人姓名')
    sprice2Partner = models.FloatField(null=True, blank=True, default=0, verbose_name='应付合作人金额')
    dealPlatform = models.CharField(max_length = 10, null=True, blank=True, verbose_name='支付平台')
    snote = models.TextField(max_length = 100, null=True, blank=True, verbose_name='备注')

    def __str__(self):
        return self.customer.name + '(' + self.service.name + ':' + self.svalidFrom.strftime('%Y-%m-%d') + '--' + self.svalidTo.strftime('%Y-%m-%d') + ')'

    class Meta:
        verbose_name = '服务费订单'
        verbose_name_plural = verbose_name

class OrderType(models.Model):
    name = models.CharField(max_length=20, verbose_name='订单类型')
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '订单类型'
        verbose_name_plural = verbose_name

class District(models.Model):
    name = models.CharField(max_length = 50, verbose_name='所属区县')
    def __str__(self):
        return self.name    

    class Meta:
        verbose_name = '所属区县'
        verbose_name_plural = verbose_name

class Product_Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name='客户姓名')
    product = models.ForeignKey(Product, on_delete = models.CASCADE, verbose_name='产品名称')
    orderType = models.ForeignKey(OrderType, on_delete= models.CASCADE, default = 1, verbose_name='订单类型')
    district = models.ForeignKey(District, on_delete = models.CASCADE, default = 1, verbose_name='所属区县')

    product_base = models.FloatField(verbose_name='产品基数')
    validFrom = models.DateField(verbose_name='起始日期')
    validTo = models.DateField(verbose_name='截至日期')
    total_price = models.FloatField(verbose_name='应缴费用') 

    paymethod = models.CharField(max_length = 100,verbose_name='支付方式')
    
    orderDate = models.DateField(auto_now_add=True, verbose_name='订单日期')
    note = models.TextField(max_length = 100, null=True, blank=True, verbose_name='备注')

    def __str__(self):
        return self.customer.name + '(' + self.product.name + ':' + self.validFrom.strftime('%Y-%m-%d') + '--' + self.validTo.strftime('%Y-%m-%d') + ')'

    class Meta:
        verbose_name = '产品订单'
        verbose_name_plural = verbose_name

class Operations(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name='客户姓名')
    product = models.ForeignKey(Product, on_delete = models.CASCADE, verbose_name='产品名称')
    oper_date = models.DateTimeField(auto_now_add=True, verbose_name='操作日期')
    
    oper_Type = (
        (1,'新增'),
        (2,'续费'),
        (3, '减员'),
        )
    operation = models.PositiveSmallIntegerField(choices=oper_Type, verbose_name='所做操作')

    def __str__(self):
        return self.customer.name + '(' + self.product.name + ':' + str(self.operation) + ':' +  self.oper_date.strftime('%Y-%m-%d %H:%M:%S') + ')'

    class Meta:
        verbose_name = '操作'
        verbose_name_plural = verbose_name


class TodoList(models.Model):
    info = models.TextField(verbose_name='待办事宜', max_length=500)
    isfinished = models.BooleanField(verbose_name='是否已完成', default=False)

    def __str__(self):
        return self.info
    
    class Meta:
        verbose_name ='待办事宜'
        verbose_name_plural = verbose_name