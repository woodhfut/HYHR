from django.conf.urls import url

from . import views

app_name = 'sb'
urlpatterns = [
    url(r'^$', views.sb_index, name='sb_index'),
    url(r'^sb(?P<id>[0-9]+)/$', views.sb_subsb, name='sb_subsb'),
    url(r'^query/$', views.sb_query, name='sb_query'),
    url(r'^add/(?P<code>[1|2|4|8])/$', views.sb_add, name='sb_add'),
    url(r'^reorder/(?P<code>[1|2|4|8])/(?P<pid>(\d{6})(\d{4})(\d{2})(\d{2})(\d{3})([0-9]|X))/$', views.sb_reorder, name='sb_reorder'),
    url(r'^reorderAll/(?P<pid>(\d{6})(\d{4})(\d{2})(\d{2})(\d{3})([0-9]|X))/(?P<data>.+)/$', views.sb_reorder_all, name='sb_reorder_all'),
    url(r'^remove/(?P<code>[1|2|4|8])/$', views.sb_remove, name='sb_remove'),
    url(r'^remove/(?P<code>[1|2|4|8])/(?P<pid>(\d{6})(\d{4})(\d{2})(\d{2})(\d{3})([0-9]|X))/$', views.sb_remove_id, name='sb_reorder_id'),
    url(r'^billcheck/(?P<code>[1|2|4|8])/$', views.sb_billcheck, name='sb_billcheck'),
    url(r'^billcheckAll/$', views.sb_billcheck_all, name='sb_billcheck_all'),
    url(r'^pushclient/(?P<code>[1|2|4|8])/$', views.sb_pushclient, name='sb_pushclient'),
    url(r'^export/csv/(?P<path>\w+)/$', views.export_csv, name='export_csv'),
    url(r'^todolist/$', views.sb_todolist, name='sb_todolist'),
    url(r'^todolist/add/$', views.sb_todolist_add, name='sb_todolist_add'),
    url(r'^todolist/modify/(?P<id>\d+)/$', views.sb_todolist_modify, name='sb_todolist_modify'),
    url(r'^partnerbillcheck/$', views.sb_partnerbillcheck, name='sb_partnerbillcheck'),
    url(r'^operationquery/$', views.sb_operationquery, name='sb_operationquery'),
    url(r'^wechatbroadcast_ws/$', views.wechatbroadcast_ws, name='wechatbroadcast_ws'),
    url(r'^wechatbroadcast/$', views.WechatBroadcastView.as_view(), name='wechatbroadcast'),
]