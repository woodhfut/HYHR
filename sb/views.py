from django.shortcuts import render, HttpResponseRedirect, redirect, get_object_or_404
from django.http import HttpRequest, HttpResponse
from django.template import RequestContext
from datetime import datetime
from django.contrib.auth.views import login_required
from django.contrib.auth.decorators import user_passes_test, permission_required
from django.db import transaction
from .forms import QueryForm, CustomerForm, Product_OrderForm, Service_OrderForm
from .models import Product_Order, Customer, Product, Service_Order, Partner, OrderType, District, PayMethod
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


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


@user_passes_test(lambda u: u.is_superuser, login_url='/login/')
def sb_query(request):
    if request.POST:
        form = QueryForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            name = cd['name']
            pid = cd['pid']
            dateFrom = cd['dateFrom']
            dateTo = cd['dateTo']
            pagecount = request.POST['page_count']
            pageid = request.POST['page_id']
            if not pagecount:
                pagecount = 15
            if not pageid:
                pageid = 1

            try:
                result = Product_Order.objects.all()
                if name !='':
                    result = result.filter(customer__name__icontains=name)
                if pid !='':
                    result = result.filter(customer__pid__iexact=pid)
                if dateFrom:
                    result = result.filter(validTo__gte=dateFrom)
                if dateTo:
                    result = result.filter(validFrom__lte=dateTo)

                result = result.order_by('name')
                paginator = Paginator(result, pagecount)
                try:
                    rst = paginator.page(pageid)
                except PageNotAnInteger:
                    rst = paginator.page(1)
                except EmptyPage:
                    rst = paginator.page(paginator.num_pages)
            except:
                result = Product_Order.objects.none()
            return render(request,'app/sb_query.html',
                  {
                      'title': 'Query',
                      'pagecount': pagecount,
                      'form':form,
                      'result': rst,
                      'year': datetime.now().year
                  })

        else:
            return render(request,'app/sb_query.html',
                  {
                      'title': 'Query',
                      'pagecount': 15,
                      'form':form,
                      'year': datetime.now().year
                  })
    else:
        
        form = QueryForm()
        if 'name' in request.GET or \
            'pid' in request.GET or \
            'dateFrom' in request.GET or \
            'dateTo' in request.GET:
            name = request.GET.get('name',None)
            pid = request.GET.get('pid',None)
            dateFrom = request.GET.get('dateFrom',None)
            dateTo = request.GET.get('dateTo',None)
            pageid = request.GET.get('page_id',1)
            pagecount = request.GET.get('page_count',15)
            collapse = request.GET.get('collapse',1)
            try:
                pagecount = int(pagecount)
            except:
                pagecount = 15
            
            try:
                pageid = int(pageid)
            except:
                pageid = 1

            try:
                collapse = int(collapse)
            except:
                collapse = 1
            
            form = QueryForm({'name':name,
                          'pid':pid,
                          'dateFrom':dateFrom,
                          'dateTo':dateTo,
                          })
            if form.is_valid():
                try:
                    result = Product_Order.objects.all()
                    if name and len(name.strip()) > 0:
                
                        result = result.filter(customer__name__icontains=name)
                    if pid and len(pid.strip())> 0:
                
                        result = result.filter(customer__pid=pid)
                    if dateFrom: 
                
                        result = result.filter(validTo__gte=dateFrom)
                    if dateTo:
                
                        result = result.filter(validFrom__lte=dateTo)
                    
                    paginator = Paginator(result, pagecount)
                    try:
                        rst = paginator.page(pageid)
                    except PageNotAnInteger:
                        rst = paginator.page(1)
                    except EmptyPage:
                        rst = paginator.page(paginator.num_pages)
                except:
                    result = Product_Order.objects.none()
                    rst = Product_Order.objects.none()
                
                return render(request,'sb/sb_query.html',
                          {
                              'title': 'Query',
                              'pagecount': pagecount,
                              'collapse': collapse,
                              'result': rst,
                              'form':form,
                              'year': datetime.now().year
                          })
            else:
                return render(request,'sb/sb_query.html',
                      {
                          'title': 'Query',
                          'pagecount': pagecount,
                          'collapse': collapse,
                          'form':form,
                          'year': datetime.now().year
                      })
        else:
            return render(request,'sb/sb_query.html',
                      {
                          'title': 'Query',
                          'pagecount': 15,
                          'collapse':1,
                          'form':form,
                          'year': datetime.now().year
                      })

@user_passes_test(lambda u: u.is_superuser, login_url='/login/')
def sb_add(request):
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
                    customer, created = Customer.objects.get_or_create(
                        name = c_cd['name'],
                        pid = c_cd['pid'],
                        defaults = {
                            'phone' : c_cd['phone'],
                            'hukou' : c_cd['hukou'],
                            'wechat' : c_cd['wechat'],
                            'introducer' : c_cd['introducer'],
                            'note' : c_cd['note']
                        },
                    )
    
                    productName = p_cd['product']
                    product = Product.objects.get(name = productName)
                    
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
                        orderType = ordertype,
                        paymethod = paymtd,
                        validFrom = p_cd['validFrom'],
                        validTo = p_cd['validTo'],
                        defaults={
                            
                            'product_base' : p_cd['product_base'],
                            'total_price' : p_cd['total_price'],
                            'payaccount' : p_cd['payaccount'],
                            'orderDate' : p_cd['orderDate'],
                            'note' : p_cd['note']
                        },
                    )

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
                            'orderDate' : p_cd['orderDate'],
                            'partner': s_cd['partner'],
                        },
                    )
            except Exception as ex:
                return HttpResponse('exception met during add new order. {}'.format(ex))
            return render(request, 'sb/add_success.html',
                  {
                        'title': '添加成功',
                        'year':datetime.now().year,    
                  })
        else:
            return render(request, 'sb/sb_add.html',
                  {
                        'title':'新增',
                        'customer_form':customer_form,
                        'p_order_form': p_order_form,
                        's_order_form': s_order_form,
                        'year':datetime.now().year    
                  })
    else:
        customer_form = CustomerForm()
        p_order_form = Product_OrderForm()
        s_order_form = Service_OrderForm()
        return render(request, 'sb/sb_add.html',
                  {
                        'title': '新增',
                        'customer_form':customer_form,
                        'p_order_form': p_order_form,
                        's_order_form': s_order_form,
                        'year':datetime.now().year    
                  })


@user_passes_test(lambda u: u.is_superuser, login_url='/login/')
def sb_reorder(request,id):

    customer = get_object_or_404(Customer, pid=id)

    if request.POST:
        p_order_form = Product_OrderForm(request.POST)
        checkServiceFee = request.POST.get('chkServiceFee',False)
        latestsrecs = Service_Order.objects.filter(customer__pid = id).order_by('-svalidTo')
        latestsvcRec = None
        if len(latestsrecs) > 0:
            latestsvcRec = latestsrecs[0]
        chk = '1'
        if not checkServiceFee:
            chk = '0'
        if p_order_form.is_valid():
            p_cd = p_order_form.cleaned_data
            try:
                productName = p_cd['product']
                product = Product.objects.get(name = productName)

                paymthdname = p_cd['paymethod']
                paymtd = PayMethod.objects.get(name=paymthdname)

                dstName = p_cd['district']
                district = District.objects.get(name= dstName)

                p_order = Product_Order(
                        customer=customer, 
                        product=product,
                        validFrom = p_cd['validFrom'],
                        validTo = p_cd['validTo'],
                        district = district,
                        product_base = p_cd['product_base'],
                        total_price = p_cd['total_price'],
                        paymethod =paymtd,
                        payaccount = p_cd['payaccount'],
                        orderDate = p_cd['orderDate'],
                        note = p_cd['note']
                        )
                #order.save()
                
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
                                orderDate = p_cd['orderDate'],
                                
                                snote = s_cd['snote']
                            )
                            #s_order.save()
                            with transaction.atomic():
                                p_order.save()
                                s_order.save()
                        else:
                            
                            return render(request, 'sb/sb_reorder.html',
                            {
                                'title': '续费',
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
                                'title': '续费',
                                'customer':customer,
                                'p_order_form': p_order_form,
                                's_order_form': s_order_form,
                                'latestsvcRec': latestsvcRec,
                                'chkServiceFee':chk,
                                'year':datetime.now().year
                            })
                    
                else:
                    p_order.save()

            except Exception as ex:
                return render(request, 'HYHR/error.html',
                {
                    'errormessage': ex,
                    'year':datetime.now().year
                })
            return render(request, 'sb/reorder_success.html',
            {
                'title':'续费成功!',
                'year':datetime.now().year
            })
        else:
            s_order_form = Service_OrderForm(request.POST)            
            return render(request, 'sb/sb_reorder.html',
                            {
                                'title': '续费',
                                'customer':customer,
                                'p_order_form': p_order_form,
                                's_order_form': s_order_form,
                                'latestsvcRec': latestsvcRec,
                                'chkServiceFee':chk,
                                'year':datetime.now().year
                                })
    else:
        p_order_form = Product_OrderForm()
        s_order_form = Service_OrderForm()    
        latestsrecs = Service_Order.objects.filter(customer__pid = id).order_by('-svalidTo')
        latestsvcRec = None
        if len(latestsrecs) > 0:
            latestsvcRec = latestsrecs[0]
        
        return render(request, 'sb/sb_reorder.html',
                    {
                        'title': '续费',
                        'customer':customer,
                        'p_order_form': p_order_form,
                        's_order_form': s_order_form,
                        'latestsvcRec': latestsvcRec,
                        'year':datetime.now().year
                        })
