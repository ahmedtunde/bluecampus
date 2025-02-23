import logging
import json
from datetime import datetime
from channels.generic.websocket import AsyncWebsocketConsumer
from redis import Redis
from .models import Participant
from asgiref.sync import sync_to_async
from django.contrib.auth.models import AnonymousUser
from bluecampus.app.activity.participants_util import (
    create_or_update_participant, create_anonymous_participant,
    generate_unique_username, generate_unique_id
)

logger = logging.getLogger(__name__)
redis_conn = Redis(host='localhost', port=6379, db=0)

class VideoChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'video_chat_{self.room_id}'
        logger.debug(f"Connecting to room: {self.room_id}")

        if not self.scope["user"].is_authenticated:
            self.user_id = f'anonymous_{generate_unique_id()}'
            self.username = generate_unique_username()
            await sync_to_async(create_anonymous_participant)(self.user_id, self.room_id)
            logger.debug(f"Anonymous user created: {self.user_id}")
        else:
            self.user_id = str(self.scope["user"].id)
            self.username = self.scope["user"].username
            await sync_to_async(create_or_update_participant)(self.scope["user"], self.room_id)
            logger.debug(f"Authenticated user connected: {self.username}")

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        logger.debug(f"WebSocket accepted for user: {self.username}")

        await self.send_old_messages()
        await self.update_user_state({'audio_enabled': True, 'video_enabled': True})
        await self.get_and_send_user_states()
        await self.update_user_count()

    async def disconnect(self, close_code):
        logger.debug(f"Disconnecting user: {self.user_id}")
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        redis_conn.hdel(f'user_states_{self.room_group_name}', self.user_id)

        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'user_left',
            'user_id': self.user_id,
        })
        logger.info(f"User {self.user_id} left room {self.room_id}")

    async def receive(self, text_data):
        data = json.loads(text_data)
        logger.debug(f"Received data: {data}")

        message_type = data.get('type')
        if message_type in ['offer', 'answer', 'ice-candidate', 'chat', 'user_joined']:
            handler = getattr(self, f'handle_{message_type}', None)
            if handler:
                await handler(data)

    async def handle_offer(self, data):
        offer = data.get('offer')
        if not offer or not offer.get('sdp'):
            logger.error("Invalid offer data")
            return

        user_id = data.get('user_id') or data.get('to')
        logger.debug(f"Sending offer from {user_id}")
        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'offer',
            'sdp': offer['sdp'],
            'user_id': user_id
        })

    async def answer(self, data):
        logger.debug(f"Received answer data: {data}")

        sdp = data.get('sdp')
        user_id = data.get('user_id')

        if not sdp:
            logger.error("Invalid answer data: missing 'sdp'")
            return
        
        if not user_id:
            logger.warning("Answer received without user_id. Assigning a default value.")
            user_id = "unknown_user"

        logger.debug(f"Sending answer from {user_id} with SDP: {sdp}")
        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'answer',
            'sdp': sdp,
            'user_id': user_id
        })



    async def handle_ice_candidate(self, data):
        if not data.get('candidate'):
            logger.error("Invalid ICE candidate data")
            return

        user_id = data['user_id']
        logger.debug(f"Sending ICE candidate from {user_id}")
        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'ice_candidate',
            'candidate': data['candidate'],
            'user_id': user_id
        })

    async def handle_chat(self, data):
        message = data.get('message', '')
        timestamp = datetime.utcnow().isoformat()
        chat_data = {
            'user_id': self.user_id,
            'username': self.username,
            'message': message,
            'timestamp': timestamp,
        }
        logger.debug(f"Chat message from {self.username}: {message}")

        redis_conn.rpush(f'chat_messages_{self.room_group_name}', json.dumps(chat_data))
        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'chat_message',
            'chat_data': chat_data,
        })

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat',
            'chat_data': event['chat_data']
        }))

    async def offer(self, event):
        await self.send(text_data=json.dumps({
            'type': 'offer',
            'sdp': event['sdp'],
            'user_id': event['user_id']
        }))

    async def handle_answer(self, data):
        logger.debug(f"Received answer data: {data}")
        
        answer = data.get('answer')
        if not answer or not answer.get('sdp'):
            logger.error("Invalid answer data: missing 'sdp'")
            return

        user_id = data.get('user_id')
        sdp = answer['sdp']
        logger.debug(f"Sending answer from {user_id} with SDP: {sdp}")
        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'answer',
            'sdp': sdp,
            'user_id': user_id
        })


    async def ice_candidate(self, event):
        await self.send(text_data=json.dumps({
            'type': 'ice-candidate',
            'candidate': event['candidate'],
            'user_id': event['user_id']
        }))

    async def user_left(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'user_id': event['user_id']
        }))

    async def handle_user_joined(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'user_id': event['user_id']
        }))
    async def send_old_messages(self):
        messages = redis_conn.lrange(f'chat_messages_{self.room_group_name}', 0, -1)
        for message in messages:
            await self.send(text_data=json.dumps({
                'type': 'chat_message',
                'chat_data': json.loads(message.decode('utf-8'))
            }))

    async def update_user_count(self):
        user_count = await self.get_user_count()
        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'user_count_update',
            'count': user_count
        })

    async def user_count_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_count_update',
            'count': event['count']
        }))

    async def update_user_state(self, state):
        redis_conn.hset(f'user_states_{self.room_group_name}', self.user_id, json.dumps(state))
        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'user_state_update',
            'user_id': self.user_id,
            'state': state
        })

    async def get_and_send_user_states(self):
        user_states = redis_conn.hgetall(f'user_states_{self.room_group_name}')
        for user_id, state in user_states.items():
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'user_state_update',
                'user_id': user_id.decode('utf-8'),
                'state': json.loads(state.decode('utf-8'))
            })

    async def user_state_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_state_update',
            'user_id': event['user_id'],
            'state': event['state']
        }))

    async def get_user_count(self):
        return redis_conn.hlen(f'user_states_{self.room_group_name}')
