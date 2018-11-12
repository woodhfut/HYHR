from django.conf.urls import url
from . import consumers

websocket_urlpatterns = [
    url(r'^(?i)ws/sb/wechat/$', consumers.WebchatBroadcastConsumer),
]