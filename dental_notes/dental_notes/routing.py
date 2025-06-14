from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
# from django.conf.urls import url
from django_eel.consumers import EelConsumer

application = ProtocolTypeRouter({
    "websocket": URLRouter([
        path(r"^eel$", EelConsumer),
    ]),
})