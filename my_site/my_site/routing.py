from django.urls import re_path
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from matching.consumer import StartMatching
from chat.consumer import ChatConsumer

websocket_urlpatterns = [
    re_path(r'ws/matching/(?P<location>[^/]+)/$', StartMatching.as_asgi()),
    re_path(r'ws/chat/(?P<room_name>[^/]+)/$', ChatConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})