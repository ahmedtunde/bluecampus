from channels.generic.websocket import AsyncWebsocketConsumer
import json
from asgiref.sync import sync_to_async
from .models import Participant
from channels.db import database_sync_to_async
from bluecampus.app.activity.participants_util import create_or_update_participant, create_anonymous_participant
from django.contrib.auth.models import AnonymousUser

class VideoChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'video_chat_{self.room_id}'

        if not self.scope["user"].is_authenticated:
            self.user_id = f"anonymous_{self.channel_name[:5]}"
            self.username = f"AnonymousUser{self.channel_name[:5]}"
        else:
            self.user_id = self.scope["user"].id
            self.username = self.scope["user"].username

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'user_id': self.user_id,
                'username': self.username,
            }
        )

        user_count = await self.get_user_count()
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'update_user_count',
                'user_count': user_count,
            }
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_left',
                'user_id': self.user_id,
            }
        )

        user_count = await self.get_user_count()
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'update_user_count',
                'user_count': user_count,
            }
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json['type']

        if message_type == 'join':
            await self.handle_join(text_data_json)
        elif message_type == 'offer':
            await self.handle_offer(text_data_json)
        elif message_type == 'answer':
            await self.handle_answer(text_data_json)
        elif message_type == 'ice':
            await self.handle_ice(text_data_json)
        elif message_type == 'chat':
            await self.handle_chat(text_data_json)
            
            
    async def handle_join(self, data):
        user = self.scope['user']
        if isinstance(user, AnonymousUser):
            print(user)
            await sync_to_async(create_anonymous_participant)(AnonymousUser(), self.room_id)
        else:
            await sync_to_async(create_or_update_participant)(user, self.room_id)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'user_id': self.user_id,
                'username': self.username,
            }
        )
    # async def handle_join(self, data):
    #     user = self.scope['user']
    #     await self.channel_layer.group_send(
    #         self.room_group_name,
    #         {
    #             'type': 'user_joined',
    #             'user_id': self.user_id,
    #             'username': self.username,
    #         }
    #     )

    async def handle_offer(self, data):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'send_offer',
                'offer': data['offer'],
                'from': data['from']
            }
        )

    async def handle_answer(self, data):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'send_answer',
                'answer': data['answer'],
                'from': data['from']
            }
        )

    async def handle_ice(self, data):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'send_ice',
                'candidate': data['candidate'],
                'from': data['from']
            }
        )

    async def handle_chat(self, data):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat',
                'message': data['message'],
                'username': self.username,
            }
        )

    async def user_joined(self, event):
        user = self.scope['user']
        print(event)
        if isinstance(user, AnonymousUser):
            await sync_to_async(create_anonymous_participant)(AnonymousUser(), self.room_id)
            await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'user_id': 'Anonymous_user',
            'username': 'anonymous',
            }))
        else:
            await sync_to_async(create_or_update_participant)(user, self.room_id)
            await self.send(text_data=json.dumps({
                'type': 'user_joined',
                'user_id': event['user'],
                'username': event['username'],
            }))

    async def send_offer(self, event):
        await self.send(text_data=json.dumps({
            'type': 'send_offer',
            'offer': event['offer'],
            'from': event['from'],
        }))

    async def send_answer(self, event):
        await self.send(text_data=json.dumps({
            'type': 'send_answer',
            'answer': event['answer'],
            'from': event['from'],
        }))

    async def send_ice(self, event):
        await self.send(text_data=json.dumps({
            'type': 'send_ice',
            'candidate': event['candidate'],
            'from': event['from'],
        }))

    async def chat(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat',
            'message': event['message'],
            'username': event['username'],
        }))

    async def update_user_count(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_count',
            'user_count': event['user_count'],
        }))

    @database_sync_to_async
    def get_user_count(self):
        print(self.room_id)
        return Participant.objects.filter(room_id=self.room_id).count()
