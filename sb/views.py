from django.shortcuts import render, HttpResponseRedirect, redirect, get_object_or_404
from django.http import HttpRequest, HttpResponse
from django.template import RequestContext
from datetime import datetime,date
from django.contrib.auth.views import login_required
from django.contrib.auth.decorators import user_passes_test, permission_required
from django.db import transaction
from .forms import QueryForm, CustomerForm, Product_OrderForm, Service_OrderForm, OperationQueryForm
from .models import Product_Order, Customer, Product, Service_Order, Partner, OrderType, District, \
                    Operations, User_extra_info, TodoList, Service, Company
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .Utils import ProductCode, CustomerStatusCode, CustomerOperations, SendPushMessage,\
     getNextMonthRange, BillCheckAllResult, ServiceCode, getServiceMonthRange, getPreviousMonthRange, getCurrentMonthRange
from calendar import monthrange
from wxpy import Bot
import os
from django.conf import settings
from random import randint
import threading
import multiprocessing
import time
import csv
from wsgiref.util import FileWrapper
from django.db.models import Sum, F, Q
from django.forms import formset_factory
import uuid
from django.views import View
import math
import logging
logger = logging.getLogger(__name__)




def sb_index(request):
    return render(request,'sb/index.html',
                  {
                      'title': 'sb',
                      'message':'index',
                      
                  })

@user_passes_test(lambda u: u.is_superuser, login_url='/login/')
def sb_subsb(request, id):
    return render(request,'sb/sb_index.html',
                  {
                      'title': 'sb',
                      'message': id,
                      
                  })

def export_query_csv_thread(request, rst_list, itemType):
    if request.session.get('result_file_query'):
        filename = request.session.get('result_file_query')
    else:
        filename = request.user.username + '_query.csv'
        request.session['result_file_query'] = filename
    try:
        with open(os.path.join(settings.STATICFILES_DIRS[0],'HYHR/{}'.format(filename)), 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f) 
            if itemType == 0: #Product order
                writer.writerow(['姓名', '身份证号', '手机号', '业务名称','业务类型', '所在区县', '户口性质', '基数', '总价','开始日期', '截至日期', '下单日期', '状态'])
                for rst in rst_list:               
                    item = [rst.customer.name, '"'+rst.customer.pid+'"', rst.customer.phone, rst.product.name, rst.orderType.name, rst.company.district.name, rst.customer.get_hukou_display(), rst.product_base, rst.total_price, rst.validFrom, rst.validTo, rst.orderDate, rst.customer.status]
                    writer.writerow(item)
            elif itemType == 1: #service order
                writer.writerow(['姓名', '身份证号', '手机号', '业务名称', '户口性质', '总价','开始日期', '截至日期', '下单日期', '状态'])
                for rst in rst_list:               
                    item = [rst.customer.name, '"'+rst.customer.pid+'"', rst.customer.phone, rst.product.name, rst.customer.get_hukou_display(), rst.stotal_price, rst.svalidFrom, rst.svalidTo, rst.orderDate, rst.customer.status]
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
                uei = User_extra_info.objects.filter(username=request.user.username)
                if not uei.exists():
                    raise Exception(f'当前用户{request.user.username}没有权限执行该操作！')
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
                    if int(cstatus) == 0: #only contains active clients
                        if int(itemType) == 0:
                            result = Product_Order.objects.filter(customer__status__gt = 0).order_by('-id')
                        else:
                            result = Service_Order.objects.filter(customer__status__gt = 0).order_by('-id')
                    elif int(cstatus)==1:#include all clients
                        if int(itemType) == 0:
                            result = Product_Order.objects.order_by('-id')
                        else:
                            result = Service_Order.objects.order_by('-id')
                    else:#only include disabled clients
                        if int(itemType) == 0:
                            result = Product_Order.objects.filter(customer__status = 0).order_by('-id')
                        else:
                            result = Service_Order.objects.filter(customer__status = 0).order_by('-id')
                    
                    if name and len(name.strip()) > 0:
                        result = result.filter(customer__name__icontains=name.strip())
                    if pid and len(pid.strip())> 0:
                        result = result.filter(customer__pid=pid.strip())
                    if dateFrom: 
                        if int(itemType)==0:                
                            result = result.filter(validTo__gte=form.cleaned_data['dateFrom'])
                        else:
                            result = result.filter(svalidTo__gte=form.cleaned_data['dateFrom'])
                    if dateTo:   
                        if int(itemType)==0:          
                            result = result.filter(validFrom__lte=form.cleaned_data['dateTo'])
                        else:
                            result = result.filter(svalidFrom__lte=form.cleaned_data['dateTo'])
                    
                    
                    if int(prodName) != 0 and int(itemType)==0:
                        result = result.filter(product__code = int(prodName))
                        
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
                    
                })
            else:
                return render(request,'sb/sb_query.html',
                {
                    'title': title,
                    'pagecount': pagecount,
                    'collapse': collapse,
                    'form':form,
                    
                })
        else:
            return render(request,'sb/sb_query.html',
            {
                'title': title,
                'pagecount': settings.DEFAULT_PAGE_COUNT,
                'collapse':1,
                'form':form,
                
            })
    except Exception as ex:
        logger.error('exception in export thread. {}'.format(ex))
        return render(request, 'HYHR/error.html',
        {
            'errormessage': ex,
            
        }) 

@user_passes_test(lambda u: u.is_superuser, login_url='/login/')
def sb_add(request, code):
    product = Product.objects.get(code=code)
    title = '新增{}'.format(product.name)
    if request.POST:
        customer_form = CustomerForm(request.POST)
        p_order_form = Product_OrderForm(request.POST)
        s_order_form = Service_OrderForm(request.POST) if 'chkServiceFee' not in request.POST else None
        if customer_form.is_valid() and p_order_form.is_valid() and (s_order_form== None or s_order_form.is_valid()):
            c_cd = customer_form.cleaned_data
            p_cd = p_order_form.cleaned_data
            #s_cd = s_order_form.cleaned_data
            try:   
                existedCuStatus = int(code)
                customer, created = Customer.objects.get_or_create(
                    pid = c_cd['pid'],
                    defaults = {
                        'name' : c_cd['name'],
                        'phone' : c_cd['phone'],
                        'hukou' : c_cd['hukou'],
                        'status': code,
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
                            'dup_pid_error':'错误:已经存在身份证号为{}的客户,但姓名不为{}, 请重新确认填写的身份证号是否正确.'.format(c_cd['pid'], c_cd['name']),
                                    
                        })  
                    customer.status |= existedCuStatus
                    existedCuStatus = customer.status  
                
                otName = p_cd['orderType']
                ordertype = OrderType.objects.get(name=otName)

                comName = p_cd['company']
                company = Company.objects.get(name=comName)
                paymtdName = p_cd['paymethod']

                p_order, created = Product_Order.objects.get_or_create(
                    customer=customer, 
                    product=product,
                    company = company,
                    validFrom = p_cd['validFrom'],
                    validTo = p_cd['validTo'],
                    defaults={
                        'orderType' : ordertype,
                        'paymethod' : paymtdName,    
                        'product_base' : p_cd['product_base'],
                        'total_price' : p_cd['total_price'],
                        #'payaccount' : p_cd['payaccount'],
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
                                
                    })
                if p_cd['note']:
                    ptodo, created = TodoList.objects.get_or_create(
                        info = p_cd['note'],
                        isfinished = False
                    )

                if int(code) == ProductCode.SB.value and 'chcbj' in request.POST and 'txtcbj' in request.POST:
                    cbj =Product.objects.get(code=ProductCode.CBJ.value)
                    cbj_order, created = Product_Order.objects.get_or_create(
                    customer=customer, 
                    product=cbj,
                    company = company,
                    validFrom = p_cd['validFrom'],
                    validTo = p_cd['validTo'],
                    defaults={
                        'orderType' : ordertype,
                        'paymethod' : paymtdName,    
                        'product_base' : p_cd['product_base'],
                        'total_price' : request.POST['txtcbj'],
                        #'payaccount' : p_cd['payaccount'],
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
                            'dup_date_error':'错误:此时间段已经存在{}订单.'.format(cbj.name),
                                    
                        })
                    else:
                        customer.status |= ProductCode.CBJ.value
                
                if 'chkServiceFee' not in request.POST:
                    s_cd = s_order_form.cleaned_data
                    service = Service.objects.get(code=ServiceCode.FEE.value)
                    s_order, created = Service_Order.objects.get_or_create(
                        customer = customer,
                        service = service,
                        svalidFrom = s_cd['svalidFrom'],
                        svalidTo = s_cd['svalidTo'], 
                        defaults={
                            'stotal_price': s_cd['stotal_price'], 
                            'sprice2Partner': s_cd['sprice2Partner'],
                            'snote' : s_cd['snote'],
                            'paymethod' : s_cd['paymethod'],
                            #'payaccount' : s_cd['payaccount'],
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
                            'dup_sdate_error':'错误:此时间段已经存在{}订单.'.format(service.name),
                                    
                        })
                    if s_cd['snote']:
                        stodo,created = TodoList.objects.get_or_create(
                            info = s_cd['snote'],
                            isfinished = False
                        )

                #add info to operations table
                op = Operations(customer = customer, 
                                product = product,
                                operation = CustomerOperations.ADD.value )
                
                with transaction.atomic():
                    op.save()
                    customer.save()
                    if p_cd['note']:
                        ptodo.save()
                    if 'chkServiceFee' not in request.POST:
                        if s_cd['snote']:
                            stodo.save()
                        s_order.save()
                    p_order.save()

                    
            except Exception as ex:
                return render(request, 'HYHR/error.html',
                {
                    'errormessage': ex,
                    
                })
            return render(request, 'sb/add_success.html',
                  {
                        'title': '添加成功',
                        'code':code,
                  })
        else:
            return render(request, 'sb/sb_add.html',
                  {
                        'title':title,
                        'customer_form':customer_form,
                        'p_order_form': p_order_form,
                        's_order_form': s_order_form,
                            
                  })
    else:
        customer_form = CustomerForm()
        today = date.today()
        startDate = date(today.year, today.month, 1)
        endDate = date(today.year, today.month, monthrange(today.year, today.month)[1])
        p_order_form = Product_OrderForm(initial={
            'product': product,
            'validFrom': startDate,
            'validTo': endDate
            })
        
        s_order_form = Service_OrderForm(initial={
            'svalidFrom': startDate,
            'svalidTo': endDate,
        })
        return render(request, 'sb/sb_add.html',
        {
            'title': title,
            'customer_form':customer_form,
            'p_order_form': p_order_form,
            's_order_form': s_order_form,
                
        })


Product_OrderFormSet = formset_factory(Product_OrderForm, extra=0, max_num=4)

@user_passes_test(lambda u: u.is_superuser, login_url='/login/')
def sb_reorder_all(request,pid, data):
    try:
        customer = get_object_or_404(Customer, pid=pid)
        data = list(map(lambda x: float(x), data[1:-1].split(',')))
        logger.info(f'data passed: {data}')

        if request.POST:
            formset = Product_OrderFormSet(request.POST)
            records = []
            if formset.is_valid():
                for form in formset:
                    if form.is_valid():
                        p_cd = form.cleaned_data
                        comName = p_cd['company']
                        company = Company.objects.get(name= comName)
                        productName = p_cd['product']
                        product = Product.objects.get(name=productName)
                        validTo = p_cd['validTo']
                        lastDay = monthrange(validTo.year, validTo.month)[1]
                        if validTo.day < lastDay:
                            validTo = date(validTo.year, validTo.month, lastDay)
                        p_order, pcreated  = Product_Order.objects.get_or_create(
                                customer=customer, 
                                product=product,
                                validFrom = p_cd['validFrom'],
                                validTo = validTo,
                                company = company,
                                defaults={
                                    'product_base' : p_cd['product_base'],
                                    'total_price' : p_cd['total_price'],
                                    'paymethod' : p_cd['paymethod'],
                                    #'payaccount' : p_cd['payaccount'],
                                    #orderDate = p_cd['orderDate'],
                                    'note' : p_cd['note']
                                },)
                        
                        records.append(p_order)
                        op = Operations(customer = customer,
                                            product = product,
                                            operation = CustomerOperations.REORDER.value)
                        records.append(op)

                        if p_cd['note']:
                            logger.info(f'add {p_cd["note"]} to Todolist in reorder.')
                            ptodo, created = TodoList.objects.get_or_create(
                                info = p_cd['note'],
                                isfinished = False
                            ) 
                            records.append(ptodo)
                    else:
                        raise Exception(form.errors)
                
                #need pay service fee
                if data[-2] != 0:
                    s_order_form = Service_OrderForm(request.POST)
                    if s_order_form.is_valid():
                        s_cd = s_order_form.cleaned_data
                        ###TODO: Here constrains only include situation... need more precise validation
                        service_fee = Service.objects.get(code=ServiceCode.FEE.value)
                        if not Service_Order.objects.filter(customer__pid = customer.pid,service=service_fee, 
                            svalidTo__gte=s_cd['svalidTo'], svalidFrom__lte=s_cd['svalidFrom']).exists(): 
                            spaymthdname = s_cd['paymethod']
                            svalidTo = s_cd['svalidTo']
                            lastDay = monthrange(svalidTo.year, svalidTo.month)[1]
                            if svalidTo.day < lastDay:
                                svalidTo = date(svalidTo.year, svalidTo.month, svalidTo.day)
                            s_order = Service_Order.objects.create(
                                customer = customer,
                                service = service_fee,
                                svalidFrom = s_cd['svalidFrom'],
                                svalidTo = svalidTo,
                                stotal_price = s_cd['stotal_price'],
                                paymethod =spaymthdname,
                                #payaccount = s_cd['payaccount'],
                                partner = s_cd['partner'],
                                sprice2Partner = s_cd['sprice2Partner'],
                                #orderDate = p_cd['orderDate'],
                                snote = s_cd['snote']
                            )
                            
                            if s_cd['snote']:
                                logger.info(f'add {s_cd["snote"]} to Todolist in reorder.')
                                stodo,created = TodoList.objects.get_or_create(
                                info = s_cd['snote'],
                                isfinished = False
                                )
                                records.append(stodo)
                    
                            with transaction.atomic():
                                for order in records:
                                    if not hasattr(order, 'product'):
                                        order.save()
                                        continue
                                    code = order.product.code
                                    customer.status |= code
                                    order.save()
                                s_order.save()
                            return render(request, 'sb/reorder_success.html',
                            {
                                'title':'{}续费成功!'.format(product.name),
                            })
                        else: #client has paid serivce fee
                            with transaction.atomic():
                                for order in records:
                                    code = order.product.code
                                    customer.status |= code
                                    order.save()
                                op.save()
                                if p_cd['note']:
                                    ptodo.save()
                            return render(request, 'sb/reorder_success.html',
                            {
                                'title':'{}续费成功!'.format(product.name),
                            })

                    else:
                        raise Exception(s_order_form.errors)   
                else:
                    with transaction.atomic():
                        for order in records:
                            if not hasattr(order,'product'):
                                order.save()
                                continue
                            code = order.product.code
                            customer.status |= code
                            order.save()
                    return render(request, 'sb/reorder_success.html',
                    {
                        'title':'{}续费成功!'.format(product.name),
                    })
            else:
                raise Exception(formset.errors)        
        else:
            inits = []
            s_order = None
            nextMonth = getCurrentMonthRange()
            
            for i in range(len(data)-2): #-1 is total value, -2 is fee.
                if data[i] !=0:
                    product = Product.objects.get(code=math.pow(2, i))
                    rec = Product_Order.objects.filter(customer__pid__iexact=pid, product__code=product.code).order_by('-id')[0]
                    inits.append({
                        'product': product, 
                        'total_price': data[i],
                        'validFrom': nextMonth[0],
                        'validTo': nextMonth[1],
                        'product_base': rec.product_base,
                        'paymethod': rec.paymethod,
                        })           
            
            formset = Product_OrderFormSet(initial=inits)
            s_latest_rec = None
            if data[-2]!=0:
                s_latest_rec = Service_Order.objects.filter(customer__pid__iexact=pid, service__code=ServiceCode.FEE.value).order_by('-id')[0]
                nextServiceRange = getServiceMonthRange(pid, ServiceCode.FEE.value)
                
                s_order = Service_OrderForm(initial={
                    'svalidFrom': nextServiceRange[0], 
                    'svalidTo': nextServiceRange[1],
                    'paymethod': s_latest_rec.paymethod,
                    'stotal_price': s_latest_rec.stotal_price, 
                })

            return render(request, 'sb/sb_reorder_all.html', {
                'title': f'{customer}续费', 
                'customer': customer,
                'formset': formset,
                's_order': s_order,
                's_last_record': s_latest_rec,
            })
    except Exception as ex:
        logger.error(f'error in sb_reorder_all, ex: {ex}')
        return render(request, 'HYHR/error.html',
        {
            'errormessage': ex,
            
        })

@user_passes_test(lambda u: u.is_superuser, login_url='/login/')
def sb_reorder(request,code,pid):

    customer = get_object_or_404(Customer, pid=pid)
    product = Product.objects.get(code=code)
    if request.POST:
        p_order_form = Product_OrderForm(request.POST)
        checkServiceFee = request.POST.get('chkServiceFee',False)
        logger.info(checkServiceFee)
        latestsrecs = Service_Order.objects.filter(customer__pid = pid, service__code = ServiceCode.FEE.value).order_by('-svalidTo')
        latestsvcRec = None
        if len(latestsrecs) > 0:
            latestsvcRec = latestsrecs[0]
        chk = '1'
        if not checkServiceFee:
            chk = '0'
        if p_order_form.is_valid():
            p_cd = p_order_form.cleaned_data
            try:
                paymtd = p_cd['paymethod']
                comName = p_cd['company']
                company = Company.objects.get(name= comName)

                validTo = p_cd['validTo']
                lastDay = monthrange(validTo.year, validTo.month)[1]
                if validTo.day < lastDay:
                    validTo = date(validTo.year, validTo.month, lastDay)

                p_order, pcreated  = Product_Order.objects.get_or_create(
                        customer=customer, 
                        product=product,
                        validFrom = p_cd['validFrom'],
                        validTo = validTo,
                        company = company,
                        defaults={
                            'product_base' : p_cd['product_base'],
                            'total_price' : p_cd['total_price'],
                            'paymethod' : paymtd,
                            #'payaccount' : p_cd['payaccount'],
                            #orderDate = p_cd['orderDate'],
                            'note' : p_cd['note']
                        },)
                #order.save()
                op = Operations(customer = customer,
                                            product = product,
                                            operation = CustomerOperations.REORDER.value)

                if p_cd['note']:
                    logger.info(f'add {p_cd["note"]} to Todolist in reorder.')
                    ptodo, created = TodoList.objects.get_or_create(
                        info = p_cd['note'],
                        isfinished = False
                    )
                    
                if not checkServiceFee and 'stotal_price' in request.POST: #make sure Service_order form does exist
                    #check whether service order exists.
                    s_order_form = Service_OrderForm(request.POST)
                    if s_order_form.is_valid():
                        s_cd = s_order_form.cleaned_data
                        ###TODO: Here constrains only include situation... need more precise validation
                        service_fee = Service.objects.get(code=ServiceCode.FEE.value)
                        if not Service_Order.objects.filter(customer__pid = customer.pid,service=service_fee, 
                            svalidTo__gte=s_cd['svalidTo'], svalidFrom__lte=s_cd['svalidFrom']).exists(): 
                            spaymthdname = s_cd['paymethod']
                            svalidTo = s_cd['svalidTo']
                            lastDay = monthrange(svalidTo.year, svalidTo.month)[1]
                            if svalidTo.day < lastDay:
                                svalidTo = date(svalidTo.year, svalidTo.month, svalidTo.day)
                            s_order = Service_Order.objects.create(
                                customer = customer,
                                service = service_fee,
                                svalidFrom = s_cd['svalidFrom'],
                                svalidTo = svalidTo,
                                stotal_price = s_cd['stotal_price'],
                                paymethod =spaymthdname,
                                #payaccount = s_cd['payaccount'],
                                partner = s_cd['partner'],
                                sprice2Partner = s_cd['sprice2Partner'],
                                #orderDate = p_cd['orderDate'],
                                
                                snote = s_cd['snote']
                            )
                            #s_order.save()
                            customer.status |=  product.code

                            if s_cd['snote']:
                                logger.info(f'add {s_cd["snote"]} to Todolist in reorder.')
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
                            
                        })
                    
                else:
                    customer.status |=  product.code
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
                    
                })
            return render(request, 'sb/reorder_success.html',
            {
                'title':'{}续费成功!'.format(product.name),
                'code': code,
                
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
                
                })
    else:
        p_order = Product_Order.objects.filter(product__code=code, customer__pid__iexact=pid).order_by('-id')[0]
        nextMonth = getCurrentMonthRange()
        if p_order.validFrom<= nextMonth[0] and p_order.validTo>= nextMonth[1]: #already paid next month
            p_order_form = Product_OrderForm(initial={
            'product': product,
            'product_base': p_order.product_base,
            'validFrom': p_order.validFrom,
            'validTo': p_order.validTo,
            'total_price': p_order.total_price,
            'paymethod': p_order.paymethod,
            })
        else:
            p_order_form = Product_OrderForm(initial={
                'product': product,
                'product_base': p_order.product_base,
                'validFrom': nextMonth[0],
                'validTo': nextMonth[1],
                'total_price': p_order.total_price,
                'paymethod': p_order.paymethod,
                })

        latestsrecs = Service_Order.objects.filter(customer__pid = pid, service__code=ServiceCode.FEE.value).order_by('-svalidTo')
        latestsvcRec = None
        if len(latestsrecs) > 0:
            latestsvcRec = latestsrecs[0]

        if latestsvcRec:
            if not latestsrecs.filter(svalidFrom__lte=nextMonth[0], svalidTo__gte=nextMonth[1]).exists():
                nextServiceRange = getServiceMonthRange(pid, ServiceCode.FEE.value)
                s_order_form = Service_OrderForm(initial={
                    'svalidFrom': nextServiceRange[0], 
                    'svalidTo': nextServiceRange[1],
                    'stotal_price': latestsvcRec.stotal_price,
                    'paymethod': latestsvcRec.paymethod,
                })
            else:
                s_order_form = None
        else:
            s_order_form = Service_OrderForm()    
        
        return render(request, 'sb/sb_reorder.html',
        {
            'title': '{}续费'.format(product.name),
            'customer':customer,
            'p_order_form': p_order_form,
            's_order_form': s_order_form,
            'latestsvcRec': latestsvcRec,                        
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
        try:
            #todo: if client has ordered next month of product, you are not allowed to remove it. unless refund...
            nextmonth = getCurrentMonthRange()
            startdate = nextmonth[0]
            enddate = nextmonth[1]

            if customer.status & product.code == CustomerStatusCode.Disabled.value:
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
                logger.info('{}-{}'.format(customer.status, code))
                customer.status ^=product.code
                if product.code == ProductCode.SB.value:
                    logging.info(f'try to remove sb of {customer.name}, you will also remove gs and gjj status.')
                    if customer.status& ProductCode.CBJ.value == ProductCode.CBJ.value :
                        customer.status ^= ProductCode.CBJ.value
                    if customer.status& ProductCode.GS.value == ProductCode.GS.value:
                        customer.status ^= ProductCode.GS.value

                logger.info(customer.status)
                with transaction.atomic():
                    customer.save()
                    op.save()
        except Exception as ex:
            return render(request, 'HYHR/error.html',
                {
                    'errormessage': ex,
                    
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
    
    cscode = int(code)

    customers =[c for c in Customer.objects.filter(status__gt = CustomerStatusCode.Disabled.value) if c.status & cscode == cscode]

    if len(customers):
        today = date.today()
        startdate = date(today.year, today.month, 1)
        enddate = date(today.year, today.month, monthrange(today.year, today.month)[1])
        logger.info('startdate:{}, enddate:{}'.format(startdate.strftime('%Y-%m-%d'), enddate.strftime('%Y-%m-%d')))
        porders = Product_Order.objects.filter(product__code =code,  validFrom__lte=startdate, validTo__gte=enddate,customer__in=customers)

        nextmonth = getCurrentMonthRange()
        snextmonth = nextmonth[0]
        enextmonth = nextmonth[1]
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
        with open(os.path.join(settings.STATICFILES_DIRS[0],'HYHR/{}'.format(filename)), 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f) 
            
            writer.writerow(['姓名', '身份证号', '手机号', '业务名称', '所在区县','户口性质','基数','状态'])
            for rst in rst_list:               
                item = [rst.customer.name, '"' +rst.customer.pid+'"', rst.customer.phone,  rst.product.name, rst.company.district, rst.customer.get_hukou_display(),rst.product_base, rst.customer.status]
                writer.writerow(item)
           
    except Exception as ex:
        logger.error('exception in export thread. {}'.format(ex))

def export_billcheckAll_csv_thread(request, rst_list):
    if request.session.get('result_file_billcheckAll'):
        filename = request.session.get('result_file_billcheckAll')
    else:
        filename = request.user.username + '_billcheckAll.csv'
        request.session['result_file_billcheckAll'] = filename
    try:
        with open(os.path.join(settings.STATICFILES_DIRS[0],'HYHR/{}'.format(filename)), 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f) 
            
            writer.writerow(['姓名', '社保', '公积金','个税', '残保金','服务费', '总数'])
            for rst in rst_list:               
                item = [rst.customer.name]
                item.extend(rst.records)
                writer.writerow(item)
           
    except Exception as ex:
        logger.error('exception in export thread. {}'.format(ex))


@user_passes_test(lambda u: u.is_superuser, login_url='/login/')
def sb_billcheck_all(request):
    try:
        today = date.today()
        month = today.month
        title = f'{month}月对账'

        #check all product records in previous month 
        startDate , endDate = getPreviousMonthRange()
        pOrders = Product_Order.objects.filter(validFrom__lte=startDate, validTo__gte=endDate, customer__status__gt=CustomerStatusCode.Disabled.value)

        startNextMonth , endNextMonth = getCurrentMonthRange()

        result = {}
        fee ={}
        for p in pOrders:
            if p.customer.status & p.product.code != p.product.code or Product_Order.objects.filter(customer__pid=p.customer.pid, validTo__gte=endNextMonth, product__code=p.product.code).exists():
                continue
            pos = int(math.log2(p.product.code))
            if p.customer.name not in result:
                rec = [0]*6 #sb, gjj, gs, cbj, fee, total
                rec[pos] = p.total_price
                rec[-1] = p.total_price
                result[p.customer.name] = BillCheckAllResult(p.customer, rec)
            else:
                result[p.customer.name].records[pos] = p.total_price
                result[p.customer.name].records[-1] = round(result[p.customer.name].records[-1]+p.total_price, 2)
        
            if p.customer.name not in fee and  not Service_Order.objects.filter(customer__pid=p.customer.pid, svalidFrom__lte=startNextMonth, svalidTo__gte=endNextMonth, customer__status__gt=CustomerStatusCode.Disabled.value).exists():
                lastRec = Service_Order.objects.filter(customer__pid=p.customer.pid).order_by('-id')[0]
                result[p.customer.name].records[-2] = lastRec.stotal_price
                result[p.customer.name].records[-1] = round(result[p.customer.name].records[-1] + lastRec.stotal_price, 2)
                fee[p.customer.name] = True
        
        records = [v for v in result.values()]
        if len(records) == 0:
            return render(request, 'sb/sb_billcheck_all.html',
            {
                'title': title,
                'message': '***当前户中所有客户已完成当月缴费,无需对账.***'
            })
        threading.Thread(target=export_billcheckAll_csv_thread, args=(request, records,)).start()
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
        paginator = Paginator(records, pagecount)

        try:
            rst = paginator.page(pagenum)
        except PageNotAnInteger:
            rst = paginator.page(1)            
        except EmptyPage:
            rst = paginator.page(paginator.num_pages)

        return render(request, 'sb/sb_billcheck_all.html',
        {
            'title':title,
            'porders': rst,
            'pagecount': pagecount,
        }) 
    except Exception as ex:
        logger.error(f'exception ocurred in billcheck_all, {ex}')
        return render(request, 'HYHR/error.html', {'errormessage': ex,})


@user_passes_test(lambda u: u.is_superuser, login_url='/login/')
def sb_billcheck(request, code):
    try:
        today = date.today()
        month = today.month
        product = Product.objects.get(code=code)
        title = '{}月{}对账'.format(month, product.name)

        customers =[c for c in Customer.objects.filter(status__gt = CustomerStatusCode.Disabled.value) if c.status & product.code == product.code]

        if len(customers):
            startdate, enddate = getPreviousMonthRange()
            logger.info('startdate:{}, enddate:{}'.format(startdate.strftime('%Y-%m-%d'), enddate.strftime('%Y-%m-%d')))
            porders = Product_Order.objects.filter(product__code =code,  validFrom__lte=startdate, validTo__gte=enddate,customer__in=customers).order_by('id')

            nextmonth = getCurrentMonthRange()
            snextmonth = nextmonth[0]
            enextmonth = nextmonth[1]
            
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
                vqrpath = 'HYHR/img/QR_{}.png'.format(str(uuid.uuid4()))
                if settings.DEBUG:
                    qrpath = os.path.join(settings.STATICFILES_DIRS[0], vqrpath)
                else:
                    qrpath = os.path.join(settings.STATIC_ROOT, vqrpath)
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
                        'QR': vqrpath,
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
                if msg == '':
                    msg = '寰宇向你致以亲切问候.'
                customers = getbillcheckCustomers(code)
                retry = 30
                while retry > 0:
                    if not wxpybot:
                        time.sleep(1)
                        retry -= 1
                    else: 
                        break
                if not wxpybot: 
                    return render(request, 'sb/pushclient.html',
                    {
                        'title': '发送微信信息',
                        'errormsg': '微信登录超时, 请稍后重试. 请在获取二维码30秒内扫描登录.',
                    })
                else:
                    result = SendPushMessage(wxpybot, customers, msg)
                    #logger.info('result is {}'.format(result))
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
        baseName = os.path.basename(file_route).split('.')
        response['Content-Disposition'] = f'attachment; filename={baseName[0]}{datetime.now()}.{baseName[1]}' 
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
            pname = request.GET.get('name', 'first')#FIRST TIME ENTER THE PAGE, WE DON'T SHOW ANYTHING.
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
                srecords = Service_Order.objects.exclude(Q(sprice2Partner=0)| Q(partner__name=None)).order_by('partner__name', '-id')
                #summary = Service_Order.objects.raw('select id, partner_id, sum(sprice2Partner) from sb_Service_Order where sprice2Partner <> 0 group by partner_id')
                summary = Service_Order.objects.exclude(Q(sprice2Partner=0) | Q(partner__name=None)).values('partner__name').annotate(Sum('sprice2Partner'))
                if not srecords.exists():
                    return render(request, 'sb/partnerbillcheck.html',
                    {
                        'error': '已结清与所有合伙人的费用.',
                        'pname': pname,

                    })
                else:
                    return render(request, 'sb/partnerbillcheck.html',
                    {
                        'srecords': srecords,
                        'summary': summary,
                    })     
                     
    except Exception as ex:
        return render(request, 'HYHR/error.html',
        {
            'errormessage': ex,
            
        })


@user_passes_test(lambda u: u.is_superuser, login_url='/login/')
def sb_operationquery(request):
    try:
        if 'dateFrom' in request.GET or 'dateTo' in request.GET or 'productName' in request.GET or 'opName' in request.GET:
            dateFrom = request.GET.get('dateFrom', None)
            dateTo = request.GET.get('dateTo', None)
            prodName = request.GET.get('productName', 0) #all
            opName = request.GET.get('opName', 0)
            pagecount = request.GET.get('page_count', settings.DEFAULT_PAGE_COUNT)
            pageid = request.GET.get('page_id', 1)

            opform = OperationQueryForm(
                # {
                #     'dateFrom': dateFrom,
                #     'dateTo':dateTo,
                #     'productName': prodName
                # }
                request.GET
            )
            if opform.is_valid():
                try:
                    pagecount = int(pagecount)
                except:
                    pagecount = settings.DEFAULT_PAGE_COUNT
                
                try:
                    pageid = int(pageid)
                except:
                    pageid = 1
                
                try:
                    prodName = int(prodName)
                except:
                    prodName  = 0

                try:
                    opName = int(opName)
                except:
                    opName  = 0

                result = Operations.objects.exclude(operation=CustomerOperations.REORDER.value).order_by('customer__name','-id')
                if dateFrom:
                    df = opform.cleaned_data['dateFrom']
                    result = result.filter(oper_date__gte=df)
                
                if dateTo:
                    dt = opform.cleaned_data['dateTo']
                    result = result.filter(oper_date__lte=dt)
                
                if prodName != 0:
                    result = result.filter(product__code=prodName)
                
                if opName != 0:
                    result = result.filter(operation=opName)
                
                paginator = Paginator(result, pagecount)
                try:
                    rst = paginator.page(pageid)
                except PageNotAnInteger:
                    rst = paginator.page(1)
                except EmptyPage:
                    rst = paginator.page(paginator.num_pages)

                return render(request, 'sb/operationquery.html',
                {
                    'form': opform,
                    'result': rst,
                    'pagecount': pagecount,
                    'pageid': pageid,
                }) 
                
            else:
                return render(request, 'sb/operationquery.html',
                {
                    'form': opform,
                }) 
        else:
            opform = OperationQueryForm()
            return render(request, 'sb/operationquery.html',
            {
                'form': opform,
            })
    except Exception as ex:
        return render(request, 'HYHR/error.html',
        {
            'errormessage': ex,
            
        })

WxpybotDict ={}
lock = threading.Lock()

def removeSessBot(sessid):
    with lock:
        print('about to move {}'.format(sessid))
        WxpybotDict.pop(sessid, None)
        cachefile = os.path.join(settings.WXPYCACHE_DIR, sessid+'.pkl')
        if os.path.exists(cachefile):
            print('sess pkl path exists at ' + cachefile)
            try:
                os.remove(cachefile)
            except Exception as ex:
                logger.warn('error while delete sess pkl file.{} '.format(ex))
        else:
            cachefile = os.path.join(settings.BASE_DIR, sessid+'.pkl')
            if os.path.exists(cachefile):
                print('sess pkl path exists at ' + cachefile )
                try:
                    os.remove(cachefile)
                except Exception as ex:
                    logger.warn('error while delete sess pkl file.{} '.format(ex))

def checkQRSess(request, qrpath, sessid):
    try:
        cachepath = settings.WXPYCACHE_DIR
        if not os.path.exists(cachepath):
            try:
                os.mkdir(cachepath)
            except:
                cachepath = settings.BASE_DIR
        cachefile = os.path.join(cachepath, '{}.pkl'.format(sessid))
        bot = Bot(cache_path = cachefile ,qr_path=qrpath)
        with lock:
            WxpybotDict[sessid] = bot
        threading.Timer(settings.WXPYSTATUS_DURATION, removeSessBot, args=(sessid,)).start()
        
    except Exception as ex:
        logger.warn('Error during create wxpybot. {}'.format(ex))

class WechatBroadcastView(View):
    def get(self, request, *args, **kwargs):
        global WxpybotDict
        if request.session.session_key in WxpybotDict:
            wxpybot = WxpybotDict[request.session.session_key]
            print(wxpybot)
            friends = [f.name for f in wxpybot.friends()]
            if len(friends):
                return render(request, 'sb/wechatbroadcast.html',
                {
                    'title': '发送微信信息',
                    'Friends': friends,
                })
            else:#probably logout from phone already
                WxpybotDict.pop(request.session.session_key,None)
                return render(request, 'sb/wechatbroadcast.html',
                {
                    'title': '发送微信信息',
                    'getQRCode': '1',
                    
                })
        else:
            return render(request, 'sb/wechatbroadcast.html',
            {
                'title': '发送微信信息',
                'getQRCode': '1',
                
            })

    
    def post(self, request, *args, **kwargs):
        global WxpybotDict
        if 'getFriends' in request.POST or 'sendmsg' in request.POST:
            if not request.session.session_key in WxpybotDict:
                retry = 60
                while retry > 0:
                    if request.session.session_key in WxpybotDict:
                        break
                    retry-=1
                    time.sleep(1)

                if not request.session.session_key in WxpybotDict:
                    logger.error('even after 60 sec, wechat is still not logged in. Error might happended, ask client to retry.')  
                    return render(request, 'sb/wechatbroadcast.html',
                    {
                        'title': '发送微信信息',
                        'errormsg': '获取微信登录信息超时.请在获取登录二维码后60秒内扫描登录. 如在手机上已确认登录，请刷新页面.',
                    })     
        if request.session.session_key in WxpybotDict:    
            wxpybot = WxpybotDict[request.session.session_key]       
            if 'getFriends' in request.POST:
               
                friends = [f.name for f in wxpybot.friends()]
                if len(friends):
                    return render(request, 'sb/wechatbroadcast.html',
                    {
                        'title': '发送微信信息',
                        'Friends': friends,
                    })
                else:#probably logout from phone already
                    WxpybotDict.pop(request.session.session_key,None)
                    return render(request, 'sb/wechatbroadcast.html',
                    {
                        'title': '发送微信信息',
                        'getQRCode': '1',
                        
                    })
            elif 'sendmsg' in request.POST:
                msg = request.POST.get('message', '寰宇向你致以亲切问候.')
                if msg == '':
                    msg = '寰宇向你致以亲切问候.'
                friends = request.POST.getlist('subcheckboxes')
                result = SendPushMessage(wxpybot, friends, msg)
                                       
                return render(request, 'sb/wechatbroadcast.html',
                {
                    'title': '发送微信信息',                   
                    
                    'result' : result[1]
                })
            else:
                return render(request, 'sb/wechatbroadcast.html',
                    {
                        'title': '发送微信信息',
                        'errormsg': '发送状态错误，请稍后重试.',
                    })
        else:
            if 'getQR' in request.POST:
                if not request.session.session_key:
                    request.session.save()
                print(request.session.session_key) 
                #WxpybotDict.pop(request.session.session_key,None)   
                vqrpath = 'HYHR/img/QR_{}.png'.format(request.session.session_key)
                #print('QR path {}'.format(vqrpath))
                if settings.DEBUG:
                    qrpath = os.path.join(settings.STATICFILES_DIRS[0], vqrpath)
                else:
                    qrpath = os.path.join(settings.STATIC_ROOT, vqrpath)
                
                #thread to check qr.png is downloaded
                threading.Thread(target=checkQRSess, args=(request, qrpath,request.session.session_key)).start()
                # qrpro = multiprocessing.Process(target=checkQRSess, args=(request, qrpath, uid))
                # qrpro.start()

                retry = 60
                while retry > 0:
                    if not os.path.exists(qrpath) and not request.session.session_key in WxpybotDict:
                        time.sleep(1)
                        retry-= 1
                    else:
                        break

                if os.path.exists(qrpath):
                    return render(request, 'sb/wechatbroadcast.html',
                    {
                        'title': '发送微信信息',
                        'QR': vqrpath,
                    })
                elif request.session.session_key in WxpybotDict: #here means don't need qr code, client just click confirm on the phone.
                    return render(request, 'sb/wechatbroadcast.html',
                    {
                        'title': '发送微信信息',
                        'confirm': True,
                    })
                else:
                    logger.error('still doesnot get QR after 60 sec. ')
                    # try:
                    #     if qrpro.is_alive():
                    #         qrpro.terminate()
                    # except Exception as ex:
                    #     logger.warn('Error occurred while exit qr process. {}'.format(ex))
                    return render(request, 'sb/wechatbroadcast.html',
                    {
                        'title': '发送微信信息',
                        'errormsg': '没有获取到微信登陆二维码, 请稍后重试.如在手机上已确认登录，请刷新页面.',
                    })
            else:
                return render(request, 'sb/wechatbroadcast.html',
                {
                    'title': '发送微信信息',
                    'errormsg': '发送状态错误，请稍后重试.',
                })


def wechatbroadcast_ws(request):
    return render(request, 'sb/wechatbroadcast_ws.html',{})