from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import ugettext_lazy as _
from django.forms import ModelForm
from .models import Customer, Product_Order, Service_Order
from django import forms
from datetime import datetime, date
from django.utils import timezone
from django.contrib.admin.widgets import AdminDateWidget


class CustomerForm(ModelForm):
    class Meta:
        model = Customer
        fields = '__all__'
        exclude={'status',}
        labels = {
                'name':_('姓名'),
                'pid':_('身份证号'),
                'phone':_('手机号'),
                'hukou':_('户口性质'),
                'wechat':_('微信号'),
                'introducer':_('介绍人姓名'),
                'note':_('备注'),
                
            }
        help_texts = {
                #'name': _('客户姓名'),
            }
    def clean_pid(self):
        id = self.cleaned_data.get('pid',None)
        if id:
            id = id.strip()
            if len(id) != 18 and len(id) != 15:
                raise forms.ValidationError('invalid pid length. it should be either length 15 or 18')
            elif len(id) == 15 and not id.isnumeric():
                raise forms.ValidationError('pid with length 15 should be numeric.')
            elif len(id) == 18:
                if not id[:17].isnumeric() or (id[-1].upper() != 'X' and not id[-1].isnumeric()):
                    raise forms.ValidationError('pid with length 18 should be numeric or end with X.')
        return id

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', None)
        if phone:
            phone = phone.strip()
            if len(phone) != 11:
                raise forms.ValidationError(_('手机号码必须为11位.'), code=_('invalid_length'))
        return phone

class Product_OrderForm(ModelForm):
    def clean_validTo(self):
        cdf = self.cleaned_data.get('validFrom',None)
        cdt = self.cleaned_data.get('validTo', None)
        if cdf and cdt and cdf > cdt:
            raise forms.ValidationError(_('DateTo should be bigger than DateFrom.'), code=_('invalid_date'))
        return cdt
    
    def clean_product_base(self):
        base = self.cleaned_data.get('product_base', 0.0)
        if base < 0:
            raise forms.ValidationError(_('基数必须为正数.'), code=_('invalid_value'))
        return base

    def clean_total_price(self):
        tp = self.cleaned_data.get('total_price', 0.0)
        if tp < 0:
            raise forms.ValidationError(_('总价必须为正数.'), code=_('invalid_value'))     
        return tp

    class Meta:
        model = Product_Order
        exclude =['customer','orderDate']
        labels = {
                'product':_('业务名称'),
                'orderType':_('业务类型'),
                'district':_('所属区县'),
                'validFrom':_('开始日期'),
                'validTo':_('结束日期'),
                'product_base':_('基数'),
                'total_price':_('总价'),
                'paymethod':_('支付方式'),
                'payaccount':_('支付账户'),
                #'orderDate':_('下单日期'),
                'note':_('备注'),
                
            }
        widgets={
                'validFrom':AdminDateWidget({'placeholder':'开始日期.'}),
                'validTo': AdminDateWidget({'placeholder':'结束日期.'}),
                'orderDate': AdminDateWidget({'placeholder': 'Order date.'}),
            }

class Service_OrderForm(ModelForm):
    def clean_svalidTo(self):
        cdf = self.cleaned_data.get('svalidFrom',None)
        cdt = self.cleaned_data.get('svalidTo', None)
        if cdf and cdt and cdf > cdt:
            raise forms.ValidationError(_('DateTo should be bigger than DateFrom.'), code=_('invalid_date'))
        return cdt
    
    def clean_stotal_price(self):
        tp = self.cleaned_data.get('stotal_price', 0.0)
        if tp < 0:
            raise forms.ValidationError(_('总价必须为正数.'), code=_('invalid_value'))     
        return tp
    class Meta:
        model = Service_Order
        fields=['svalidFrom', 'svalidTo', 'stotal_price', 'paymethod','payaccount','partner','sprice2Partner','snote']
        labels = {
                #'customer':_('客户姓名'),
                #'product':_('业务名称'),
                'svalidFrom':_('开始日期'),
                'svalidTo':_('结束日期'),
                'stotal_price':_('总价'),
                'paymethod':_('支付方式'),
                'payaccount':_('支付账户'),
                #'orderDate':_('下单日期'),
                'partner':_('合作伙伴'),
                'sprice2Partner':_('应给合伙人费用'),
                'snote':_('备注'),
                
            }
        widgets={
                'svalidFrom':AdminDateWidget({'placeholder':'开始日期.'}),
                'svalidTo': AdminDateWidget({'placeholder':'结束日期.'}),
                'orderDate': AdminDateWidget({'placeholder': '缴纳日期.'}),
            } 
        
class QueryForm(forms.Form):
    name = forms.CharField(required =False, max_length=30,
                           widget=forms.TextInput({
                               'class': 'form-control',
                               'placeholder':'Customer name',
                               'help_text':'Enter customer name.'}))

    pid = forms.CharField(required = False, max_length=18, min_length=15, 
                          widget=forms.TextInput({
                               'class': 'form-control',
                               'placeholder':'PID'}))
    dateFrom = forms.DateField(required =False,
                              widget= AdminDateWidget({
                                  
                                  'placeholder':'Date From',}))
    dateTo = forms.DateField(required =False,
                             widget=AdminDateWidget({
                               
                               'placeholder':'Date To',}))
    
    def clean_name(self):
        cname = self.cleaned_data.get('name',None)
        return cname

    def clean_pid(self):
        id = self.cleaned_data.get('pid',None)
        if id:
            id = id.strip()
            if len(id) != 18 and len(id) != 15:
                raise forms.ValidationError('invalid pid length. it should be either length 15 or 18')
            elif len(id) == 15 and not id.isnumeric():
                raise forms.ValidationError('pid with length 15 should be numeric.')
            elif len(id) == 18:
                if not id[:17].isnumeric() or (id[-1].upper() != 'X' and not id[-1].isnumeric()):
                    raise forms.ValidationError('pid with length 18 should be numeric or end with X.')
        return id
    '''
    def clean(self):
        cd = super(QueryFrom,self).clean()
        cdf = cd.get('dateFrom', date(1970,1,1))
        cdt = cd.get('dateTo', date.today())
        if cdf and cdt and cdf >= cdt:
            raise forms.ValidationError(_('Invalid date selected for DateFrom.'), code=_('invalid_date'))
        return cd
     '''

    def clean_dateTo(self):
        cdf = self.cleaned_data.get('dateFrom',None)
        cdt = self.cleaned_data.get('dateTo', None)
        if cdf and cdt and cdf > cdt:
            raise forms.ValidationError(_('DateTo should be bigger than DateFrom.'), code=_('invalid_date'))
        return cdt
    