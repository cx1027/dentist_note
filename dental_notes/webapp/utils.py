from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def trigger_send_data():
    # count = 100
    content = "hello"
    return content