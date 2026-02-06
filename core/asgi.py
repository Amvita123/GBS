import os
import django

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from chatapp.urls import ws_urlpatterns
from channels.routing import ProtocolTypeRouter, URLRouter
from middleware import JWTAuthMiddlewareStack

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    "websocket": JWTAuthMiddlewareStack(URLRouter(ws_urlpatterns))
})


