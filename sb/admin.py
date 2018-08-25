from django.contrib import admin

# Register your models here.
from .models import Customer, Product, Product_Order, Service_Order, Partner, User_extra_info,District, OrderType

admin.site.register(Customer)
admin.site.register(Product)
admin.site.register(Product_Order)
admin.site.register(Service_Order)
admin.site.register(Partner)
admin.site.register(District)
admin.site.register(OrderType)
admin.site.register(User_extra_info)