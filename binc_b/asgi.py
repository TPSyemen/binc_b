"""
ASGI config for binc_b project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
<<<<<<< HEAD
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import realtime.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'binc_b.settings')

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(
            realtime.routing.websocket_urlpatterns
        )
    ),
})
=======

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'binc_b.settings')

application = get_asgi_application()
>>>>>>> 6656d3bd9d71955b890ca4afc248ccb86607c740
