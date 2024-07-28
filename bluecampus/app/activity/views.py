from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, status
from .models import Room, Participant, Message, Recording, Reaction, Forum, Activity
from .serializers import RoomSerializer, ParticipantSerializer, MessageSerializer, RecordingSerializer, ReactionSerializer, ForumSerializer, ActivitySerializer
from bluecampus.app.feed.models import Post, Topic
from bluecampus.app.feed.serializers import PostSerializer, TopicSerializer
import random
import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.shortcuts import render


def room_view(request, room_id):
    return render(request, 'room.html', {'room_id': room_id})

class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        room = serializer.save(host=self.request.user)
        # Notify clients of new room creation
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'video_chat_{room.id}',
            {
                'type': 'user_joined',
                'message': f'Room {room.title} has been created.'
            }
        )

    @action(detail=True, methods=['post'], url_path='join')
    def join_room(self, request, pk=None):
        room = self.get_object()
        participant, created = Participant.objects.get_or_create(user=request.user, room=room)
        if created:
            # Notify others in the room about the new participant
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'video_chat_{room.id}',
                {
                    'type': 'user_joined',
                    'message': f'User {request.user.username} has joined the room.'
                }
            )
        return Response({'message': 'Joined room successfully'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='leave')
    def leave_room(self, request, pk=None):
        room = self.get_object()
        participant = Participant.objects.filter(user=request.user, room=room).first()
        if participant:
            participant.delete()
            # Notify others in the room about the participant leaving
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'video_chat_{room.id}',
                {
                    'type': 'user_left',
                    'message': f'User {request.user.username} has left the room.'
                }
            )
            return Response({'message': 'Left room successfully'}, status=status.HTTP_200_OK)
        return Response({'error': 'You are not a participant of this room'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='raise-hand')
    def raise_hand(self, request, pk=None):
        room = self.get_object()
        participant = Participant.objects.filter(user=request.user, room=room).first()
        if participant:
            participant.role = 'speaker'
            participant.save()
            # Notify others in the room about the role change
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'video_chat_{room.id}',
                {
                    'type': 'user_joined',
                    'message': f'User {request.user.username} has raised their hand.'
                }
            )
            return Response({'message': 'Hand raised successfully'}, status=status.HTTP_200_OK)
        return Response({'error': 'You are not a participant of this room'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='accept-speaker')
    def accept_speaker(self, request, pk=None):
        room = self.get_object()
        user_id = request.data.get('user_id')
        participant = Participant.objects.filter(user__id=user_id, room=room).first()
        if participant:
            participant.role = 'speaker'
            participant.save()
            # Notify the participant and others in the room about the role change
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'video_chat_{room.id}',
                {
                    'type': 'user_joined',
                    'message': f'Participant {participant.user.username} has been accepted as a speaker.'
                }
            )
            return Response({'message': 'Participant accepted as speaker'}, status=status.HTTP_200_OK)
        return Response({'error': 'Participant not found'}, status=status.HTTP_400_BAD_REQUEST)



class ParticipantViewSet(viewsets.ModelViewSet):
    queryset = Participant.objects.all()
    serializer_class = ParticipantSerializer
    permission_classes = [IsAuthenticated]

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class RecordingViewSet(viewsets.ModelViewSet):
    queryset = Recording.objects.all()
    serializer_class = RecordingSerializer
    permission_classes = [IsAuthenticated]

class ReactionViewSet(viewsets.ModelViewSet):
    queryset = Reaction.objects.all()
    serializer_class = ReactionSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ForumViewSet(viewsets.ModelViewSet):
    queryset = Forum.objects.all()
    serializer_class = ForumSerializer

class ActivityViewSet(viewsets.ModelViewSet):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer

class DashboardViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard(self, request):
        user = request.user
        # Fetch visibility from user profile, if not present, consider all visibilities
        visibility = request.query_params.get('visibility', None) or getattr(user, 'visibility', None)
        visibility_levels = ['global', 'national', 'institution']

        # If no visibility is specified, consider all visibility levels
        if not visibility:
            visibility = random.choice(visibility_levels)

        # Fetch suggested rooms based on user interests and visibility
        rooms = list(Room.objects.filter(
            is_active=True,
            visibility=visibility,
            tags__in=user.interests.all()
        ).distinct())

        # Ensure at least 5 to 10 rooms by adding random rooms if necessary
        if len(rooms) < 5:
            additional_rooms = list(Room.objects.filter(
                visibility__in=visibility_levels
            ).exclude(id__in=[room.id for room in rooms]).order_by('?')[:5 - len(rooms)])
            rooms.extend(additional_rooms)


        # Fetch suggested forums based on user interests and visibility
        forums = list(Forum.objects.filter(
            visibility=visibility,
            interests__in=user.interests.all()
        ).distinct())


        # Ensure at least 5 to 10 posts by adding random posts if necessary
        if len(forums) < 5:
            additional_forums = list(Forum.objects.filter(
                visibility__in=visibility_levels
            ).exclude(id__in=[forum.id for forum in forums]).order_by('?')[:5 - len(forums)])
            forums.extend(additional_forums)

        # Fetch posts based on user interests and visibility
        posts = list(Post.objects.filter(
            visibility=visibility,
            tags__in=user.interests.all()
        ).distinct())

        # Ensure at least 5 to 10 posts by adding random posts if necessary
        if len(posts) < 5:
            additional_posts = Post.objects.filter(
                visibility__in=visibility_levels
            ).exclude(id__in=[post.id for post in posts]).order_by('?')[:5 - len(posts)]
            posts.extend(additional_posts)

        # Fetch activities (e.g., likes, comments)
        activities = Activity.objects.filter(user=user)

        # Serialize data
        room_serializer = RoomSerializer(rooms, many=True)
        forum_serializer = ForumSerializer(forums, many=True)
        post_serializer = PostSerializer(posts, many=True)
        activity_serializer = ActivitySerializer(activities, many=True)

        return Response({
            'rooms': room_serializer.data,
            'forums': forum_serializer.data,
            'posts': post_serializer.data,
            'activities': activity_serializer.data
        }, status=status.HTTP_200_OK)