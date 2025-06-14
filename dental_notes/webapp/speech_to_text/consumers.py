import json
from channels.generic.websocket import WebsocketConsumer

class TranscriptionConsumer(WebsocketConsumer):
    def connect(self):
        # self.room_group_name = 'test'

        # async_to_sync(self.channel_layer.group_add)(
        #     self.room_group_name,
        #     self.channel_name
        # )

        self.accept()
        
        self.send(text_data=json.dumps({
            'type':'connection_established565',
            'message':'You are now connected!'
        }))
   

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        print(message)
        # async_to_sync(self.channel_layer.group_send)(
        #     self.room_group_name,
        #     {
        #         'type':'chat_message',
        #         'message':message
        #     }
        # )

    def chat_message(self, event):
        message = event['message']

        self.send(text_data=json.dumps({
            'type':'chat',
            'message':message
        }))
    
    def send_json(self, text_data):
        # Send text data as JSON to the WebSocket
        self.send(text_data)