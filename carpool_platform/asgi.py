"""
ASGI config for carpool_platform project with Django Channels support.
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carpool_platform.settings')

# Initialize Django ASGI application early to ensure the AppRegistry is loaded
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import apps.rides.routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            apps.rides.routing.websocket_urlpatterns
        )
    ),
})
