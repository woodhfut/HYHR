from django.conf.urls import url

from . import views

app_name = 'sb'
urlpatterns = [
    url(r'^$', views.sb_index, name='sb_index'),
    url(r'^sb(?P<id>[0-9]+)/$', views.sb_subsb, name='sb_subsb'),
    url(r'^query/$', views.sb_query, name='sb_query'),
    url(r'^add/$', views.sb_add, name='sb_add'),
    url(r'^reorder/(?P<id>(\d{6})(\d{4})(\d{2})(\d{2})(\d{3})([0-9]|X))/$', views.sb_reorder, name='sb_reorder'),

]