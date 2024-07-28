# rooms/routing.py

from django.urls import re_path
from bluecampus.app.activity import consumer

websocket_urlpatterns = [
    re_path(r'ws/video_chat/(?P<room_id>\d+)/$', consumer.VideoChatConsumer.as_asgi()),
]