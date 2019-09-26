from django.shortcuts import render, HttpResponseRedirect
from datetime import datetime

import HYHR.forms
from django.db import transaction
from django.contrib.auth.admin import User
from sb.models import User_extra_info



def home(request):
    return render(request, 'HYHR/index.html',
                  {'title': 'Home',
                   })

def contact(request):
    return render(request, 'HYHR/contact.html',
                  {'title':'Contact',
                   'message':'Message for Contact page...'
                   })

def about(request):
    return render(request, 'HYHR/about.html',
                  {
                      'title': 'About',
                      'message': 'About message.'
                  })

def register(request):
    if request.POST:
        form = HYHR.forms.RegisterForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            try:
                with transaction.atomic():
                    user = User.objects.create_user(username=cd['username'], password=cd['password'])
                    user.save()
                    uei = User_extra_info.objects.create(
                        username= cd['username'],
                        pid = cd['pid'],
                        phone = cd['phoneNo'],
                        realname = cd['realname'],
                        comment=cd['comment'])
                    uei.save()
                return HttpResponseRedirect('/login/')
            except Exception as ex:
                 return render(request, 'HYHR/register_form.html',
                          {
                              'form': form,
                              'title': 'Register',
                              'message': 'Errors occurred while register, please contact site administrator..' + str(ex),
                              
                          })
        else:
            #error from clean, normally password not match...     
            return render(request, 'HYHR/register_form.html',
                          {
                              'form': form,
                              'title': 'Register',
                              
                          })
    else:
        form = HYHR.forms.RegisterForm()
        return render(request, 'HYHR/register_form.html',
                  {
                      'form': form,
                      'title':'Register',
                  })