from django.shortcuts import render, HttpResponseRedirect, redirect, get_object_or_404
from django.http import HttpRequest, HttpResponse
from django.template import RequestContext
from datetime import datetime
from django.contrib.auth.views import login_required
from django.contrib.auth.decorators import user_passes_test, permission_required
from django.db import transaction
from .forms import QueryForm, CustomerForm, Product_OrderForm, Service_OrderForm
from .models import Product_Order, Customer, Product, Service_Order, Partner
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def sb_index(request):
    return render(request,'sb/index.html',
                  {
                      'title': 'sb',
                      'message':'index',
                      'year': datetime.now().year
                  })

def sb_subsb(request, id):
    return render(request,'sb/index.html',
                  {
                      'title': 'sb',
                      'message': id,
                      'year': datetime.now().year
                  })

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
                result = Order.objects.all()
                if name !='':
                    result = result.filter(customer__name__icontains=name)
                if pid !='':
                    result = result.filter(customer__pid__iexact=pid)
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
                result = Order.objects.none()
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
                    
                    p_order, created = Product_Order.objects.get_or_create(
                        customer=customer, 
                        product=product,
                        validFrom = p_cd['validFrom'],
                        validTo = p_cd['validTo'],
                        defaults={
                            'district': p_cd['district'],
                            'product_base' : p_cd['product_base'],
                            'total_price' : p_cd['total_price'],
                            'paymethod' : p_cd['paymethod'],
                            'payaccount' : p_cd['payaccount'],
                            'orderDate' : p_cd['orderDate'],
                            'partner': p_cd['partner'],
                            'price2Partner': p_cd['price2Partner'],
                            'dealPlatform' : p_cd['dealPlatform'],
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
                            'paymethod' : p_cd['paymethod'],
                            'payaccount' : p_cd['payaccount'],
                            'orderDate' : p_cd['orderDate'],
                            'partner': p_cd['partner'],
                            'dealPlatform' : p_cd['dealPlatform']
                        },
                    )
            except:
                return HttpResponse('failed...')
            return render(request, 'sb/sb_add.html',
                  {
                        'title':'Add Successfully.',
                        'customer_form':customer_form,
                        'p_order_form': p_order_form,
                        's_order_form': s_order_form,
                        'year':datetime.now().year    
                  })
        else:
            return render(request, 'sb/sb_add.html',
                  {
                        'title':'Add',
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
                        'title': 'Add',
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
        if p_order_form.is_valid():
            p_cd = p_order_form.cleaned_data
            try:
                productName = p_cd['product']
                product = Product.objects.get(name = productName)
                p_order = Product_Order(
                        customer=customer, 
                        product=product,
                        validFrom = p_cd['validFrom'],
                        validTo = p_cd['validTo'],
                        district = p_cd['district'],
                        product_base = p_cd['product_base'],
                        total_price = p_cd['total_price'],
                        paymethod =p_cd['paymethod'],
                        payaccount = p_cd['payaccount'],
                        partner = p_cd['partner'],
                        price2Partner = p_cd['price2Partner'],
                        orderDate = p_cd['orderDate'],
                        dealPlatform = p_cd['dealPlatform'],
                        note = p_cd['note']
                        )
                #order.save()

                #check whether service order exists.
                if not Service_Order.objects.filter(customer__pid = customer.pid, product=product, svalidTo__gte = p_cd['validTo']).exists():
                    s_order_form = Service_OrderForm(request.POST)
                    if s_order_form.is_valid():
                        s_cd = s_order_form.cleaned_data
                        s_order = Service_Order.objects.create(
                            customer = customer,
                            product = product,
                            validFrom = s_cd['svalidFrom'],
                            validTo = s_cd['svalidTo'],
                            total_price = s_cd['stotal_price'],
                            paymethod =p_cd['paymethod'],
                            payaccount = p_cd['payaccount'],
                            partner = p_cd['partner'],
                            price2Partner = s_cd['sprice2Partner'],
                            orderDate = p_cd['orderDate'],
                            dealPlatform = p_cd['dealPlatform'],
                            note = s_cd['snote']
                        )
                        #s_order.save()
                        with transaction.atomic():
                            p_order.save()
                            s_order.save()
                    else:
                        return HttpResponse('error in service order....')

            except:
                return HttpResponse('Error......')
            return HttpResponse('success!')
        else:
            return render(request, 'sbapp/sb_reorder.html',
                          {
                              'customer':customer,
                              'order_form': p_order_form,
                              'year':datetime.now().year
                              })
    else:
        p_order_form = Product_OrderForm()
        s_order_form = Service_OrderForm()    
        return render(request, 'sb/sb_reorder.html',
                        {
                            'customer':customer,
                            'p_order_form': p_order_form,
                            's_order_form': s_order_form,
                            'year':datetime.now().year
                            })
