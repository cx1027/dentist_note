"""
ASGI config for mywebsite project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import webapp.routing
# import cwebsocket.routing


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_notes.settings')

application = ProtocolTypeRouter({
    "http":get_asgi_application(),
    "websocket":AuthMiddlewareStack(
        # URLRouter(
        #     cwebsocket.routing.websocket_urlpatterns
        # )
        URLRouter(
            webapp.routing.websocket_urlpatterns
        )
    )
})