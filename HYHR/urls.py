"""HYHR URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView

from datetime import datetime

from . import views
from . import forms

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', views.home, name='home' ),
    url(r'^contact$', views.contact, name='contact'),
    url(r'^about$', views.about, name='about'),
    url(r'^login/$',
        LoginView.as_view(template_name ='HYHR/login.html'),
        {
            #'template_name': 'HYHR/login.html',
            'authentication_form': forms.BootstrapAuthenticationForm,
            'extra_context':
            {
                'title': 'Log in',
                'year': datetime.now().year,
            }
        },
        name='login'),

    url(r'logout/$', LogoutView.as_view(template_name = 'HYHR/logout.html'),
        {
            #'template_name': 'HYHR/logout.html',
            'extra_context':
            {
                'title': 'Logout',
                'year': datetime.now().year,
                
            },
        }, name='logout'),

    url(r'register/',views.register, name='register'),


    url(r'^sb/', include('sb.urls')),
]
