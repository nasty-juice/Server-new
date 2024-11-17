import os
from django.urls import re_path
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

from matching.consumer import StartMatching
from chat.consumer import ChatConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'my_site.settings')

django_asgi_app = get_asgi_application()

websocket_urlpatterns = [
    re_path(r'ws/matching/(?P<location>[^/]+)/$', StartMatching.as_asgi()),
    re_path(r"ws/chat/(?P<room_name>[\w\-]+)/$", ChatConsumer.as_asgi()),
]

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(
                URLRouter(
                    websocket_urlpatterns,
                )
            )
        ),
    }
)