from django.shortcuts import render, HttpResponseRedirect, redirect, get_object_or_404
from django.http import HttpRequest, HttpResponse
from django.template import RequestContext
from datetime import datetime,date
from django.contrib.auth.views import login_required
from django.contrib.auth.decorators import user_passes_test, permission_required
from django.db import transaction
from .forms import QueryForm, CustomerForm, Product_OrderForm, Service_OrderForm
from .models import Product_Order, Customer, Product, Service_Order, Partner, OrderType, District, PayMethod, Operations, User_extra_info, TodoList
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .Utils import ProductCode, CustomerStatusCode, CustomerOperations, SendPushMessage
from calendar import monthrange
from wxpy import *
import os
from django.conf import settings
from random import randint
import threading
import time
import csv
from wsgiref.util import FileWrapper
from django.db.models import Sum, F
import logging
logger = logging.getLogger(__name__)




def sb_index(request):
    return render(request,'sb/index.html',
                  {
                      'title': 'sb',
                      'message':'index',
                      'year': datetime.now().year
                  })
'''
def sb_subsb(request, id):
    return render(request,'sb/index.html',
                  {
                      'title': 'sb',
                      'message': id,
                      'year': datetime.now().year
                  })
'''
@user_passes_test(lambda u: u.is_superuser, login_url='/login/')
def sb_subsb(request, id):
    return render(request,'sb/sb_index.html',
                  {
                      'title': 'sb',
                      'message': id,
                      'year': datetime.now().year
                  })

def export_query_csv_thread(request, rst_list, itemType):
    if request.session.get('result_file_query'):
        filename = request.session.get('result_file_query')
    else:
        filename = request.user.username + '_query.csv'
        request.session['result_file_query'] = filename
    try:
        with open(os.path.join(settings.STATICFILES_DIRS[0],'HYHR/{}'.format(filename)), 'w', encoding='gb2312') as f:
            writer = csv.writer(f) 
            if itemType == 0: #Product order
                writer.writerow(['姓名', '身份证号', '手机号', '业务名称','业务类型', '所在区县', '户口性质', '基数', '总价','开始日期', '截至日期', '下单日期', '状态'])
                for rst in rst_list:               
                    item = [rst.customer.name, rst.customer.pid, rst.customer.phone, rst.product.name, rst.orderType, rst.district, rst.customer.get_hukou_display(), rst.product_base, rst.total_price, rst.validFrom, rst.validTo, rst.orderDate, rst.customer.status]
                    writer.writerow(item)
            elif itemType == 1: #service order
                writer.writerow(['姓名', '身份证号', '手机号', '业务名称', '户口性质', '总价','开始日期', '截至日期', '下单日期', '状态'])
                for rst in rst_list:               
                    item = [rst.customer.name, rst.customer.pid, rst.customer.phone, rst.product.name, rst.customer.get_hukou_display(), rst.stotal_price, rst.svalidFrom, rst.svalidTo, rst.orderDate, rst.customer.status]
                    writer.writerow(item)
            else:
                raise Exception('invalid item type {}'.format(itemType))    
        
    except Exception as ex:
        logger.error('exception in export thread. {}'.format(ex))
        
@user_passes_test(lambda u: u.is_authenticated, login_url='/login/')
def sb_query(request):      
    try:
        form = QueryForm()
        title = '查询'
        if 'name' in request.GET or \
            'pid' in request.GET or \
            'dateFrom' in request.GET or \
            'dateTo' in request.GET or \
            'productName' in request.GET or \
            'customerStatus' in request.GET or \
            'itemType' in request.GET:
            name = request.GET.get('name',None)
            pid = request.GET.get('pid',None)
            dateFrom = request.GET.get('dateFrom',None)
            dateTo = request.GET.get('dateTo',None)
            prodName = request.GET.get('productName', 0)
            cstatus = request.GET.get('customerStatus', 0)
            itemType = request.GET.get('itemType', 0)
            pageid = request.GET.get('page_id',1)
            pagecount = request.GET.get('page_count',settings.DEFAULT_PAGE_COUNT)
            collapse = request.GET.get('collapse',1)
            try:
                pagecount = int(pagecount)
            except:
                pagecount = settings.DEFAULT_PAGE_COUNT
            
            try:
                pageid = int(pageid)
            except:
                pageid = 1

            try:
                collapse = int(collapse)
            except:
                collapse = 1
            
            if not request.user.is_superuser:
                uei = User_extra_info.objects.get(username=request.user.username)
                name = uei.realname
                pid = uei.pid

            form = QueryForm({'name':name,
                            'pid':pid,
                            'dateFrom':dateFrom,
                            'dateTo':dateTo,
                            'productName': int(prodName), 
                            'customerStatus': int(cstatus),
                            'itemType': int(itemType),
                            })
            if form.is_valid():
                try:
                    if int(cstatus) == 0:
                        if int(itemType) == 0:
                            result = Product_Order.objects.filter(customer__status__gt = 0).order_by('customer__name','-id')
                        else:
                            result = Service_Order.objects.filter(customer__status__gt = 0).order_by('customer__name','-id')
                    else:
                        if int(itemType) == 0:
                            result = Product_Order.objects.order_by('customer__name','-id')
                        else:
                            result = Service_Order.objectsorder_by('customer__name','-id')
                    
                    if name and len(name.strip()) > 0:
                        result = result.filter(customer__name__icontains=name)
                    if pid and len(pid.strip())> 0:
                        result = result.filter(customer__pid=pid)
                    if dateFrom:                 
                        result = result.filter(validTo__gte=form.cleaned_data['dateFrom'])
                    if dateTo:             
                        result = result.filter(validFrom__lte=form.cleaned_data['dateTo'])
                    
                    
                    if int(prodName) != 0:
                        result = result.filter(product__code = int(prodName))

                    if int(cstatus) == 0:
                        result =[r for r in result if r.product.code & r.customer.status != CustomerStatusCode.Disabled.value]
                        
                    threading.Thread(target=export_query_csv_thread, args=(request, result,int(itemType))).start()

                    paginator = Paginator(result, pagecount)
                    try:
                        rst = paginator.page(pageid)
                    except PageNotAnInteger:
                        rst = paginator.page(1)
                    except EmptyPage:
                        rst = paginator.page(paginator.num_pages)
                except Exception as ex:
                    logger.warn('Query get exception {}'.format(ex))
                    if int(itemType) == 0:
                        result = Product_Order.objects.none()
                        rst = Product_Order.objects.none()
                    else:
                        result = Service_Order.objects.none()
                        rst = Service_Order.objects.none()
                
                return render(request,'sb/sb_query.html',
                            {
                                'title': title,
                                'pagecount': pagecount,
                                'collapse': collapse,
                                'result': rst,
                                'form':form,
                                'itemType': str(itemType),
                                'year': datetime.now().year
                            })
            else:
                return render(request,'sb/sb_query.html',
                        {
                            'title': title,
                            'pagecount': pagecount,
                            'collapse': collapse,
                            'form':form,
                            'year': datetime.now().year
                        })
        else:
            return render(request,'sb/sb_query.html',
                        {
                            'title': title,
                            'pagecount': 15,
                            'collapse':1,
                            'form':form,
                            'year': datetime.now().year
                        })
    except Exception as ex:
        logger.error('exception in export thread. {}'.format(ex))
        return render(request, 'HYHR/error.html',
        {
            'errormessage': ex,
            'year':datetime.now().year
        }) 

@user_passes_test(lambda u: u.is_superuser, login_url='/login/')
def sb_add(request, code):
    product = Product.objects.get(code=code)
    title = '新增{}'.format(product.name)
    if request.POST:
        customer_form = CustomerForm(request.POST)
        p_order_form = Product_OrderForm(request.POST)
        s_order_form = Service_OrderForm(request.POST)
        if customer_form.is_valid() and p_order_form.is_valid() and s_order_form.is_valid():
            c_cd = customer_form.cleaned_data
            p_cd = p_order_form.cleaned_data
            s_cd = s_order_form.cleaned_data
            try:
                with transaction.atomic():
                    #use the product from id, ignore what is selected.
                    statusvalue = CustomerStatusCode.Disabled
                    if product.code == ProductCode.SB.value:#sb
                        statusvalue = CustomerStatusCode.SB
                    elif product.code == ProductCode.GJJ.value:#gjj
                        statusvalue = CustomerStatusCode.GJJ
                    elif product.code == ProductCode.GS.value:
                        statusvalue = CustomerStatusCode.GS

                    existedCuStatus = statusvalue.value

                    customer, created = Customer.objects.get_or_create(
                        pid = c_cd['pid'],
                        defaults = {
                            'name' : c_cd['name'],
                            'phone' : c_cd['phone'],
                            'hukou' : c_cd['hukou'],
                            'status': statusvalue.value,
                            'wechat' : c_cd['wechat'],
                            'introducer' : c_cd['introducer'],
                            'note' : c_cd['note']
                        },
                    )
                    if not created:#if customer already exists, add the new status to it
                        if customer.name != c_cd['name']:
                            return render(request, 'sb/sb_add.html',
                            {
                                    'title':title,
                                    'customer_form':customer_form,
                                    'p_order_form': p_order_form,
                                    's_order_form': s_order_form,
                                    'dup_pid_error':'错误:已经存在身份证号为{},姓名为{}的客户, 请重新确认填写的身份证号是否正确.'.format(c_cd['pid'], customer.name),
                                    'year':datetime.now().year    
                            })
                        existedCuStatus = customer.status    
                        newStaValue = customer.status | statusvalue.value
                        customer.status = newStaValue
                        #customer.save()
                    
                    otName = p_cd['orderType']
                    ordertype = OrderType.objects.get(name=otName)

                    dstName = p_cd['district']
                    district = District.objects.get(name=dstName)

                    paymtdName = p_cd['paymethod']
                    paymtd = PayMethod.objects.get(name=paymtdName)

                    p_order, created = Product_Order.objects.get_or_create(
                        customer=customer, 
                        product=product,
                        district = district,
                        validFrom = p_cd['validFrom'],
                        validTo = p_cd['validTo'],
                        defaults={
                            'orderType' : ordertype,
                            'paymethod' : paymtd,    
                            'product_base' : p_cd['product_base'],
                            'total_price' : p_cd['total_price'],
                            'payaccount' : p_cd['payaccount'],
                            #'orderDate' : p_cd['orderDate'],
                            'note' : p_cd['note']
                        },
                    )
                    if not created and existedCuStatus != CustomerStatusCode.Disabled.value:
                        return render(request, 'sb/sb_add.html',
                            {
                                    'title':title,
                                    'customer_form':customer_form,
                                    'p_order_form': p_order_form,
                                    's_order_form': s_order_form,
                                    'dup_date_error':'错误:此时间段已经存在{}订单.'.format(product.name),
                                    'year':datetime.now().year    
                            })

                    s_order, created = Service_Order.objects.get_or_create(
                        customer = customer,
                        product = product,
                        svalidFrom = s_cd['svalidFrom'],
                        svalidTo = s_cd['svalidTo'], 
                        defaults={
                            'stotal_price': s_cd['stotal_price'], 
                            'sprice2Partner': s_cd['sprice2Partner'],
                            'snote' : s_cd['snote'],
                            'paymethod' : s_cd['paymethod'],
                            'payaccount' : s_cd['payaccount'],
                            #'orderDate' : p_cd['orderDate'],
                            'partner': s_cd['partner'],
                        },
                    )

                    if not created and existedCuStatus != CustomerStatusCode.Disabled.value:
                        return render(request, 'sb/sb_add.html',
                            {
                                    'title':title,
                                    'customer_form':customer_form,
                                    'p_order_form': p_order_form,
                                    's_order_form': s_order_form,
                                    'dup_sdate_error':'错误:此时间段已经存在{}订单.'.format(product.name),
                                    'year':datetime.now().year    
                            })
                    #add info to operations table
                    op = Operations(customer = customer, 
                                    product = product,
                                    operation = CustomerOperations.ADD.value )
                    op.save()
                    customer.save()

                    logger.info('add info to Todolist.')
                    if p_cd['note']:
                        ptodo, created = TodoList.objects.get_or_create(
                            info = p_cd['note'],
                            isfinished = False
                        )
                        ptodo.save()
                    if s_cd['snote']:
                        stodo,created = TodoList.objects.get_or_create(
                            info = s_cd['snote'],
                            isfinished = False
                        )
                        stodo.save()

            except Exception as ex:
                return render(request, 'HYHR/error.html',
                {
                    'errormessage': ex,
                    'year':datetime.now().year
                })
            return render(request, 'sb/add_success.html',
                  {
                        'title': '添加成功',
                        'code':code,
                        'year':datetime.now().year,    
                  })
        else:
            return render(request, 'sb/sb_add.html',
                  {
                        'title':title,
                        'customer_form':customer_form,
                        'p_order_form': p_order_form,
                        's_order_form': s_order_form,
                        'year':datetime.now().year    
                  })
    else:
        customer_form = CustomerForm()
        p_order_form = Product_OrderForm(initial={'product': product})
        
        s_order_form = Service_OrderForm()
        return render(request, 'sb/sb_add.html',
                  {
                        'title': title,
                        'customer_form':customer_form,
                        'p_order_form': p_order_form,
                        's_order_form': s_order_form,
                        'year':datetime.now().year    
                  })


@user_passes_test(lambda u: u.is_superuser, login_url='/login/')
def sb_reorder(request,code,pid):

    customer = get_object_or_404(Customer, pid=pid)
    product = Product.objects.get(code=code)
    if request.POST:
        p_order_form = Product_OrderForm(request.POST)
        checkServiceFee = request.POST.get('chkServiceFee',False)
        latestsrecs = Service_Order.objects.filter(customer__pid = pid, product__code = code).order_by('-svalidTo')
        latestsvcRec = None
        if len(latestsrecs) > 0:
            latestsvcRec = latestsrecs[0]
        chk = '1'
        if not checkServiceFee:
            chk = '0'
        if p_order_form.is_valid():
            p_cd = p_order_form.cleaned_data
            try:
                # productName = p_cd['product']
                # product = Product.objects.get(name = productName)

                paymthdname = p_cd['paymethod']
                paymtd = PayMethod.objects.get(name=paymthdname)

                dstName = p_cd['district']
                district = District.objects.get(name= dstName)

                p_order, pcreated  = Product_Order.objects.get_or_create(
                        customer=customer, 
                        product=product,
                        validFrom = p_cd['validFrom'],
                        validTo = p_cd['validTo'],
                        district = district,
                        defaults={
                            'product_base' : p_cd['product_base'],
                            'total_price' : p_cd['total_price'],
                            'paymethod' : paymtd,
                            'payaccount' : p_cd['payaccount'],
                            #orderDate = p_cd['orderDate'],
                            'note' : p_cd['note']
                        },)
                #order.save()
                op = Operations(customer = customer,
                                            product = product,
                                            operation = CustomerOperations.REORDER.value)
                logger.info('add info to Todolist in reorder.')
                if p_cd['note']:
                    ptodo, created = TodoList.objects.get_or_create(
                        info = p_cd['note'],
                        isfinished = False
                    )
                    
                if not checkServiceFee:
                    #check whether service order exists.
                    s_order_form = Service_OrderForm(request.POST)
                    if s_order_form.is_valid():
                        s_cd = s_order_form.cleaned_data
                        ###TODO: Here constrains only include situation... need more precise validation
                        if not Service_Order.objects.filter(customer__pid = customer.pid,product=product, 
                            svalidTo__gte=s_cd['svalidTo'], svalidFrom__lte=s_cd['svalidFrom']).exists(): 
                            spaymthdname = s_cd['paymethod']
                            spaymtd = PayMethod.objects.get(name=paymthdname)

                            s_order = Service_Order.objects.create(
                                customer = customer,
                                product = product,
                                svalidFrom = s_cd['svalidFrom'],
                                svalidTo = s_cd['svalidTo'],
                                stotal_price = s_cd['stotal_price'],
                                paymethod =spaymtd,
                                payaccount = s_cd['payaccount'],
                                partner = s_cd['partner'],
                                sprice2Partner = s_cd['sprice2Partner'],
                                #orderDate = p_cd['orderDate'],
                                
                                snote = s_cd['snote']
                            )
                            #s_order.save()
                            customer.status = customer.status | product.code

                            if s_cd['snote']:
                                stodo,created = TodoList.objects.get_or_create(
                                info = s_cd['snote'],
                                isfinished = False
                                )
                    
                            with transaction.atomic():
                                p_order.save()
                                s_order.save()
                                op.save()
                                customer.save()
                                if p_cd['note']:
                                    ptodo.save()
                                if s_cd['snote']:
                                    stodo.save()
                        else:                            
                            return render(request, 'sb/sb_reorder.html',
                            {
                                'title': '{}续费'.format(product.name),
                                'customer':customer,
                                'p_order_form': p_order_form,
                                's_order_form': s_order_form,
                                'latestsvcRec': latestsvcRec,
                                'chkServiceFee': chk,
                                'dateValidError' : '错误：客户已经支付过所选时间段的服务费',
                                'year':datetime.now().year
                                })
                    else:
                        return render(request, 'sb/sb_reorder.html',
                            {
                                'title': '{}续费'.format(product.name),
                                'customer':customer,
                                'p_order_form': p_order_form,
                                's_order_form': s_order_form,
                                'latestsvcRec': latestsvcRec,
                                'chkServiceFee':chk,
                                'year':datetime.now().year
                            })
                    
                else:
                    customer.status = customer.status | product.code
                    with transaction.atomic():    
                        p_order.save()
                        op.save()
                        customer.save()
                        if p_cd['note']:
                            ptodo.save()

            except Exception as ex:
                return render(request, 'HYHR/error.html',
                {
                    'errormessage': ex,
                    'year':datetime.now().year
                })
            return render(request, 'sb/reorder_success.html',
            {
                'title':'{}续费成功!'.format(product.name),
                'code': code,
                'year':datetime.now().year
            })
        else:
            s_order_form = Service_OrderForm(request.POST)            
            return render(request, 'sb/sb_reorder.html',
                            {
                                'title': '{}续费'.format(product.name),
                                'customer':customer,
                                'p_order_form': p_order_form,
                                's_order_form': s_order_form,
                                'latestsvcRec': latestsvcRec,
                                'chkServiceFee':chk,
                                'year':datetime.now().year
                                })
    else:
        
        p_order_form = Product_OrderForm(initial={'product': product})
        s_order_form = Service_OrderForm()    
        latestsrecs = Service_Order.objects.filter(customer__pid = pid, product__code=code).order_by('-svalidTo')
        latestsvcRec = None
        if len(latestsrecs) > 0:
            latestsvcRec = latestsrecs[0]
        
        return render(request, 'sb/sb_reorder.html',
                    {
                        'title': '{}续费'.format(product.name),
                        'customer':customer,
                        'p_order_form': p_order_form,
                        's_order_form': s_order_form,
                        'latestsvcRec': latestsvcRec,
                        'year':datetime.now().year
                        })


@user_passes_test(lambda u: u.is_superuser, login_url='/login/')
def sb_remove(request,code):
    try:
        product = Product.objects.get(code=code)
        title = '{}减员'.format(product.name)
        if request.POST:
            name = request.POST.get('name', None)
            pid = request.POST.get('pid', None)

            if not name and not pid:
                return render(request, 'sb/sb_remove.html',
                {
                    'title': title,
                    'error':'错误：姓名和身份证号至少提供一项.',

                })
            else:
                customers = Customer.objects.filter(status__gt = CustomerStatusCode.Disabled.value)
                productOrders = Product_Order.objects.filter(product__code = code)

                if name:
                    customers = customers.filter(name__iexact = name)
                    productOrders = productOrders.filter(customer__name__iexact=name)
                if pid:
                    customers = customers.filter(pid = pid)
                    productOrders = productOrders.filter(customer__pid__iexact = pid)
                

                if customers.exists():
                    if productOrders.exists():
                        for cst in customers:
                            if not productOrders.filter(customer__pid__iexact = cst.pid).exists() or cst.status & int(code) == CustomerStatusCode.Disabled.value:
                                customers = customers.exclude(pid = cst.pid)
                        if len(customers) > 0:
                            return render(request, 'sb/sb_remove.html',
                            {
                                'title': title,
                                'cname':name,
                                'cpid':pid,
                                'customers': customers
                            })
                        else:
                            return render(request, 'sb/sb_remove.html',
                            {
                                'title': title,
                                'cname':name,
                                'cpid':pid,
                                'error':'错误：该客户没有{}订单或者已经减员.'.format(product.name),

                            })
                    else:
                        return render(request, 'sb/sb_remove.html',
                        {
                            'title': title,
                            'cname':name,
                            'cpid':pid,
                            'error':'错误：该客户没有{}订单.'.format(product.name),

                        })
                else:
                    return render(request, 'sb/sb_remove.html',
                    {
                        'title': title,
                        'cname':name,
                        'cpid':pid,
                        'error':'错误：该客户不存在或者已经减员.',

                    })
        else:
            return render(request, 'sb/sb_remove.html',
            {
                'title': title,
            })
    except Exception as ex:
        return render(request, 'HYHR/error.html',
                {
                    'errormessage': ex,
                    'year':datetime.now().year
                })
    

@user_passes_test(lambda u: u.is_superuser, login_url='/login/')
def sb_remove_id(request,code, pid):
    product = Product.objects.get(code = code)
    customer = Customer.objects.get(pid=pid)
    title = '确认{}减员'.format(product.name)
    op = Operations(customer = customer, 
                    product = product,
                    operation = CustomerOperations.REMOVE.value)
    if request.POST:
        cstatus2remove = CustomerStatusCode.Disabled
        if product.code == ProductCode.SB.value:
            cstatus2remove = CustomerStatusCode.SB
        elif product.code == ProductCode.GJJ.value:
            cstatus2remove = CustomerStatusCode.GJJ
        elif product.code == ProductCode.GS.value:
            cstatus2remove = CustomerStatusCode.GS
        
        try:
            #todo: if client has ordered next month of product, you are not allowed to remove it. unless refund...
            today = date.today()
            startdate = date(today.year, today.month+1, 1)
            enddate = date(today.year, today.month+1, monthrange(today.year, today.month+1)[1])

            if customer.status & cstatus2remove.value == CustomerStatusCode.Disabled.value:
                return render(request, 'sb/sb_remove_confirm.html',
                {
                    'title' : title,
                    'cname': customer.name,
                    'cpid': customer.pid,
                    'errormsg' : '错误：客户{}没有{}订单或者已经减员.'.format(customer.name, product.name )
                })
            elif Product_Order.objects.filter(product__code=code, customer__pid=pid, validFrom__lte=startdate, validTo__gte=enddate).exists():
                logger.info('customer {} already has {} order for next month, should not remove now.'.format(customer.name, product.name))
                return render(request, 'sb/sb_remove_confirm.html',
                {
                    'title' : title,
                    'cname': customer.name,
                    'cpid': customer.pid,
                    'errormsg' : '错误：客户{}已经缴纳了下个月的{}费用，请先退费以后再减员.'.format(customer.name, product.name )
                })
            
            else:
                logger.info('{}-{}'.format(customer.status, cstatus2remove.value))
                customer.status = customer.status^cstatus2remove.value
                logger.info(customer.status)
                with transaction.atomic():
                    customer.save()
                    op.save()
        except Exception as ex:
            return render(request, 'HYHR/error.html',
                {
                    'errormessage': ex,
                    'year':datetime.now().year
                })
        return render(request, 'sb/sb_remove_success.html',
        {
            'title':'成功减员',
            'pname': product.name,
            'cname': customer.name,
            'cpid': customer.pid,
            'code': code
        })
    else:
        return render(request, 'sb/sb_remove_confirm.html',
        {
            'title':title,
            'cname': customer.name,
            'cpid': customer.pid
        })
        
def getbillcheckCustomers(code):
    month = datetime.now().month
    product = Product.objects.get(code=code)
    
    cscode = CustomerStatusCode.Disabled
    if product.code == ProductCode.SB.value:
        cscode = CustomerStatusCode.SB
    elif product.code == ProductCode.GJJ.value:
        cscode = CustomerStatusCode.GJJ
    elif product.code == ProductCode.GS.value:
        cscode = CustomerStatusCode.GS

    customers =[c for c in Customer.objects.filter(status__gt = CustomerStatusCode.Disabled.value) if c.status & cscode.value == cscode.value]

    if len(customers):
        today = date.today()
        startdate = date(today.year, today.month, 1)
        enddate = date(today.year, today.month, monthrange(today.year, today.month)[1])
        logger.info('startdate:{}, enddate:{}'.format(startdate.strftime('%Y-%m-%d'), enddate.strftime('%Y-%m-%d')))
        porders = Product_Order.objects.filter(product__code =code,  validFrom__lte=startdate, validTo__gte=enddate,customer__in=customers)

        snextmonth = date(today.year, today.month+1, 1)
        enextmonth = date(today.year, today.month+1, monthrange(today.year, today.month+1)[1])
        for c in customers:
            if Product_Order.objects.filter(customer=c, product__code=code, validFrom__lte=snextmonth, validTo__gte=enextmonth).exists():
                porders = porders.exclude(customer=c, product__code = code)
        return [po.customer.name for po in porders]
    else:
        return []

def export_billcheck_csv_thread(request, rst_list):
    if request.session.get('result_file_billcheck'):
        filename = request.session.get('result_file_billcheck')
    else:
        filename = request.user.username + '_billcheck.csv'
        request.session['result_file_billcheck'] = filename
    try:
        with open(os.path.join(settings.STATICFILES_DIRS[0],'HYHR/{}'.format(filename)), 'w', encoding='gb2312') as f:
            writer = csv.writer(f) 
            
            writer.writerow(['姓名', '身份证号', '手机号','微信', '业务名称', '所在区县','户口性质','基数','状态'])
            for rst in rst_list:               
                item = [rst.customer.name, rst.customer.pid, rst.customer.phone, rst.customer.wechat, rst.product.name, rst.district, rst.customer.get_hukou_display(),rst.product_base, rst.customer.status]
                writer.writerow(item)
           
    except Exception as ex:
        logger.error('exception in export thread. {}'.format(ex))
                
@user_passes_test(lambda u: u.is_superuser, login_url='/login/')
def sb_billcheck(request, code):
    try:
        month = datetime.now().month
        product = Product.objects.get(code=code)
        title = '{}月{}对账'.format(month, product.name)
        cscode = CustomerStatusCode.Disabled
        if product.code == ProductCode.SB.value:
            cscode = CustomerStatusCode.SB
        elif product.code == ProductCode.GJJ.value:
            cscode = CustomerStatusCode.GJJ
        elif product.code == ProductCode.GS.value:
            cscode = CustomerStatusCode.GS

        customers =[c for c in Customer.objects.filter(status__gt = CustomerStatusCode.Disabled.value) if c.status & cscode.value == cscode.value]

        if len(customers):
            today = date.today()
            startdate = date(today.year, today.month, 1)
            enddate = date(today.year, today.month, monthrange(today.year, today.month)[1])
            logger.info('startdate:{}, enddate:{}'.format(startdate.strftime('%Y-%m-%d'), enddate.strftime('%Y-%m-%d')))
            porders = Product_Order.objects.filter(product__code =code,  validFrom__lte=startdate, validTo__gte=enddate,customer__in=customers).order_by('id')

            snextmonth = date(today.year, today.month+1, 1)
            enextmonth = date(today.year, today.month+1, monthrange(today.year, today.month+1)[1])
            for c in customers:
                if Product_Order.objects.filter(customer=c, product__code=code, validFrom__lte=snextmonth, validTo__gte=enextmonth).exists():
                    porders = porders.exclude(customer=c, product__code = code)

            if not len(porders):
                return render(request, 'sb/sb_billcheck.html',
                {
                    'title': title,
                    'message': '***当前户中所有客户已缴纳下月{},无需对账.***'.format(product.name)
                })

            threading.Thread(target=export_billcheck_csv_thread, args=(request, porders,)).start()    
            pagecount = settings.DEFAULT_PAGE_COUNT
            pagenum = 1
            
            if request.POST:
                pagecount = request.POST.get('page_count', pagecount)
                pagenum = request.POST.get('page_id', pagenum)
                
                try:
                    pagecount = int(pagecount)
                except:
                    pagecount = settings.DEFAULT_PAGE_COUNT
                try:
                    pagenum = int(pagenum)
                except:
                    pagenum = 1
            
            paginator = Paginator(porders, pagecount)
            try:
                rst = paginator.page(pagenum)
            except PageNotAnInteger:
                rst = paginator.page(1)            
            except EmptyPage:
                rst = paginator.page(paginator.num_pages)

            return render(request, 'sb/sb_billcheck.html',
            {
                'title':title,
                'porders': rst,
                'pagecount': pagecount,
                'code' : code
            }) 
        else:
            return render(request, 'sb/sb_billcheck.html',
            {
                'title': title,
                'message': '***当前户中没有{}客户,无需对账.***'.format(product.name)
            })
    except Exception as ex:
        return render(request, 'HYHR/error.html',
        {
            'errormessage': ex,
            'year':datetime.now().year
        })

wxpybot = None


def checkQR(qrpath):
    global wxpybot
    try:
        wxpybot = Bot(qr_path=qrpath)
    except Exception as ex:
        logger.warn('Error while generate QR for bot. {}'.format(ex))
        

@user_passes_test(lambda u: u.is_superuser, login_url='/login/')
def sb_pushclient(request, code):
    try:
        global wxpybot
        if request.POST:           
            if not wxpybot and 'getQR' in request.POST:
                qrpath = os.path.join(settings.STATICFILES_DIRS[0], 'HYHR/img/QR.png')
                if os.path.exists(qrpath):
                    try:
                        os.remove(qrpath)
                    except Exception as ex:
                        logger.warn('Error while tried to remvoe existing QR.png. ex={}'.format(ex))
                
                #thread to check qr.png is downloaded
                qrThread = threading.Thread(target=checkQR, args=(qrpath,))
                qrThread.start()
                
                retry = 20
                while retry > 0:
                    if not os.path.exists(qrpath):
                        time.sleep(1)
                        retry-= 1
                    else:
                        break

                if os.path.exists(qrpath):
                    customers = getbillcheckCustomers(code)
                    return render(request, 'sb/pushclient.html',
                    {
                        'title': '发送微信信息',
                        'QR': qrpath,
                        'customers': customers
                    })
                else:
                    logger.error('still doesnot get QR after 20 sec. ')
                    
                    return render(request, 'sb/pushclient.html',
                    {
                        'title': '发送微信信息',
                        'errormsg': '没有获取到微信登陆二维码, 请稍后重试.',
                    })
            else:
                msg = request.POST.get('message', '寰宇向你致以亲切问候.')
                customers = getbillcheckCustomers(code)
                result = SendPushMessage(wxpybot, customers, msg)
                wxpybot = None
                return render(request, 'sb/pushclient.html',
                {
                    'title': '发送微信信息',                   
                    
                    'result' : result[1]
                })
        else:   
            wxpybot = None     
            return render(request, 'sb/pushclient.html',
            {
                'title': '发送微信信息',
                'getQRCode': '1',
                
            })
    except Exception as ex:
        return render(request, 'HYHR/error.html',
        {
            'errormessage': ex,
            'year':datetime.now().year
        })
     
def export_csv(request, path):
    if request.session.get('result_file_{}'.format(path)):
        try:
            filename = request.session['result_file_{}'.format(path)]
            file_route = os.path.join(settings.STATICFILES_DIRS[0],'HYHR/{}'.format(filename))
            wrapper     = FileWrapper(open(file_route, 'rb'))

        except IOError as ex:
            return HttpResponse(ex)
        response    = HttpResponse(wrapper,content_type='application/octet-stream')
        response['Content-Disposition'] = 'attachment; filename=%s' % os.path.basename(file_route)
        response['Content-Length']      = os.path.getsize(file_route)
        return response
    else:
        return HttpResponse('{} result lost.'.format(path))


@user_passes_test(lambda u: u.is_superuser, login_url='/login/')
def sb_todolist(request):
    try:
        if request.POST:
            todoids = request.POST.getlist('subcheckboxes')
            TodoList.objects.filter(id__in=todoids).update(isfinished=True)
            return HttpResponseRedirect('.')
            
        else:
            todos = TodoList.objects.filter(isfinished=False)
            
            if todos.exists():
                return render(request, 'sb/todolist.html',
                {
                    'todos': todos,
                })
            else:
                return render(request, 'sb/todolist.html',
                {
                    'alldone': '***目前没有待办事宜!'
                })
    except Exception as ex:
        return render(request, 'HYHR/error.html',
        {
            'errormessage': ex,
            'year':datetime.now().year
        })



@user_passes_test(lambda u: u.is_superuser, login_url='/login/')
def sb_todolist_add(request):
    try:
        title = '新增待办事宜'
        if request.POST:
            info = request.POST.get('info', None)
            if info:
                info = info.strip()
                if len(info) == 0:
                    return render(request, 'sb/todolist_add_modify.html',
                    {
                        'title': title,
                        'errormsg':'是不是傻，待办事宜别空着啊！',        
                    }) 
                else:
                    todo, created = TodoList.objects.get_or_create(
                        info = info,
                        isfinished = False
                    )
                    if not created:
                        return render(request, 'sb/todolist_add_modify.html',
                        {
                            'title': title,
                            'errormsg':'是不是傻，存在相同的待办事宜还没有完成，先把那个完成了再说吧！',        
                        })
                    else:
                        todo.save()
                        return render(request, 'sb/todolist_add_success.html')
            else:
                return render(request, 'sb/todolist_add_modify.html',
                {
                    'title': title,
                    'errormsg':'是不是傻，待办事宜别空着啊！',        
                }) 
        else:
            return render(request, 'sb/todolist_add_modify.html',
            {
                'title': title,
            })
    except Exception as ex:
        return render(request, 'HYHR/error.html',
        {
            'errormessage': ex,
            'year':datetime.now().year
        })

@user_passes_test(lambda u: u.is_superuser, login_url='/login/')
def sb_todolist_modify(request, id):
    try:
        title ='修改待办事宜'
        if request.POST:
            info = request.POST.get('info', None)
            if info:
                info = info.strip()
                if len(info) == 0:
                    return render(request, 'sb/todolist_add_modify.html',
                    {
                        'title': title,
                        'errormsg':'是不是傻，待办事宜别空着啊！',        
                    })
                else:
                    todo = TodoList.objects.get(id=id)
                    todo.info = info
                    todo.save()
                    return HttpResponseRedirect('/sb/todolist/')
            else:
                return render(request, 'sb/todolist_add_modify.html',
                {
                    'title': title,
                    'errormsg':'是不是傻，待办事宜别空着啊！',        
                })
        else:
            return render(request, 'sb/todolist_add_modify.html',
            {
                'title': title,
            })

    except Exception as ex:
        return render(request, 'HYHR/error.html',
        {
            'errormessage': ex,
            'year':datetime.now().year
        }) 


@user_passes_test(lambda u: u.is_superuser, login_url='/login/')
def sb_partnerbillcheck(request):
    try:
        if request.POST:
            pname = request.POST.get('partnerName', '')
            sorderlist = request.POST.getlist('subcheckboxes')
            Service_Order.objects.filter(id__in=sorderlist).update(sprice2Partner=0)

            return HttpResponseRedirect('./?next=/&name={}'.format(pname))
        else:
            pname = request.GET.get('name', 'first')
            if pname and pname !='first':
                pexists = Partner.objects.filter(name=pname).exists()
                if not pexists:
                    return render(request, 'sb/partnerbillcheck.html', 
                    {
                        'error': '不存在该合伙人.',
                        'pname' : pname,
                    })
                else:                   
                    srecords = Service_Order.objects.filter(partner__name = pname).exclude(sprice2Partner=0).order_by('partner__name', '-id')
                    if not srecords.exists():
                        return render(request, 'sb/partnerbillcheck.html',
                        {
                            'error': '与该合伙人的费用已结清或者不曾有交易往来.',
                            'pname': pname,

                        })
                    else:
                        summary = Service_Order.objects.filter(partner__name = pname).exclude(sprice2Partner=0).values('partner__name').annotate(Sum('sprice2Partner'))
                        return render(request, 'sb/partnerbillcheck.html',
                        {
                            'pname': pname,
                            'srecords': srecords,
                            'summary': summary,
                        })   
            elif pname == 'first':
                return render(request, 'sb/partnerbillcheck.html') 
                   
            else:
                srecords = Service_Order.objects.exclude(sprice2Partner=0).order_by('partner__name', '-id')
                #summary = Service_Order.objects.raw('select id, partner_id, sum(sprice2Partner) from sb_Service_Order where sprice2Partner <> 0 group by partner_id')
                summary = Service_Order.objects.exclude(sprice2Partner=0).values('partner__name').annotate(Sum('sprice2Partner'))
                return render(request, 'sb/partnerbillcheck.html',
                {
                    'srecords': srecords,
                    'summary': summary,
                })     
                     
    except Exception as ex:
        return render(request, 'HYHR/error.html',
        {
            'errormessage': ex,
            'year':datetime.now().year
        }) 