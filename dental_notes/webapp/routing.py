from django.urls import re_path 
# from consumers import TranscriptionConsumer
from . import consumers

websocket_urlpatterns = [
    # todo!!!
    # re_path(r'ws/socket-server/', audio_transcriber.AudioTranscriber.as_asgi())
    re_path(r'ws/socket-server/', consumers.TranscriptionConsumer.as_asgi())
]