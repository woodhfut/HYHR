from django.contrib import admin

# Register your models here.
from .models import Customer, Product, Product_Order, Service_Order, Partner,\
     User_extra_info,District, OrderType, PayMethod, Operations, TodoList, \
         Service, Company

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    search_fields = ['name']


@admin.register(Product_Order)
class Product_Order_Admin(admin.ModelAdmin):
    search_fields = ['customer__name']

@admin.register(Service_Order)
class Service_Order_Admin(admin.ModelAdmin):
    search_fields = ['customer__name']

#admin.site.register(CustomerAdmin)
admin.site.register(Product)
#admin.site.register(Product_Order)
#admin.site.register(Service_Order)
admin.site.register(Partner)
admin.site.register(District)
admin.site.register(OrderType)
admin.site.register(PayMethod)
admin.site.register(Operations)
admin.site.register(User_extra_info)
admin.site.register(TodoList)
admin.site.register(Service)
admin.site.register(Company)