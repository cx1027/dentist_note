from channels.generic.websocket import AsyncWebsocketConsumer
import json
from channels.layers import get_channel_layer

class TranscriptionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("your_group", self.channel_name)
        await self.accept()
        
        # 发送默认欢迎消息和关键词
        await self.send(text_data=json.dumps({
            'message': 'Welcome to Dental Notes! Start recording to begin transcription.',
            'detect_keywords': ['Dental Assistant']  # 默认关键词
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("your_group", self.channel_name)

    async def send_message(self, event):
        # 现在处理 message 和 detect_keywords
        message = event['message']
        detect_keywords = event.get('detect_keywords', [])  # 获取关键词列表
        
        # 发送包含转录文本和关键词的消息
        await self.send(text_data=json.dumps({
            'message': message,
            'detect_keywords': detect_keywords
        }))
    