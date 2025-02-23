from uuid import uuid4
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status, viewsets, serializers
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import viewsets, status
from .models import Room, Participant, Message, Recording, Reaction, Forum, Activity, ContentType, CalendarEvent, Attendee, ForumPost, ForumComment, ForumFollow
from .serializers import AttendeeSerializer, CalendarEventSerializer, RoomSerializer, ParticipantSerializer, MessageSerializer, RecordingSerializer, ReactionSerializer, ForumSerializer, ActivitySerializer, ForumCommentSerializer, ForumPostSerializer, ForumFollowSerializer
from bluecampus.app.feed.models import Notification, Post, Topic, Visibility, Comment
from bluecampus.app.feed.serializers import PostSerializer, TopicSerializer, CommentSerializer
import random
from django.core.exceptions import PermissionDenied
import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.shortcuts import get_object_or_404, render
from django.utils.timezone import now
from rest_framework.views import APIView


def room_view(request, room_id):
    return render(request, 'room.html', {'room_id': room_id})

class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer

    def get_permissions(self):
        if self.action in ['create', 'perform_create']:
            self.permission_classes = [IsAuthenticated]
        else:
            self.permission_classes = [AllowAny]
        return super().get_permissions()

    # Custom action to return sorted rooms
    @action(detail=False, methods=['get'], url_path='sorted-rooms', permission_classes=[IsAuthenticated])
    def get_sorted_rooms(self, request):
        current_time = now()

        # Fetch rooms created by the user
        my_rooms = Room.objects.filter(host=request.user)

        # Ongoing rooms (start time <= now <= end time)
        ongoing_rooms = Room.objects.filter(scheduled_at__lte=current_time, end_time__gte=current_time)

        # Upcoming rooms (start time > now)
        upcoming_rooms = Room.objects.filter(scheduled_at__gt=current_time)
        previous_rooms = Room.objects.filter(scheduled_at__lte=current_time)
        # Serialize each category
        my_rooms_serializer = RoomSerializer(my_rooms, many=True)
        ongoing_rooms_serializer = RoomSerializer(ongoing_rooms, many=True)
        upcoming_rooms_serializer = RoomSerializer(upcoming_rooms, many=True)
        previous_rooms_serializer = RoomSerializer(previous_rooms, many=True)
        return Response({
            'my_rooms': my_rooms_serializer.data,
            'ongoing_rooms': ongoing_rooms_serializer.data,
            'upcoming_rooms': upcoming_rooms_serializer.data,
            'previous_rooms': previous_rooms_serializer.data

        }, status=status.HTTP_200_OK)
    
    # Room creation logic
    def perform_create(self, serializer):
        visibility_id = self.request.data.get('visibility')

        try:
            visibility = Visibility.objects.get(id=visibility_id)
        except Visibility.DoesNotExist:
            raise serializers.ValidationError({'visibility': 'Invalid visibility ID'})

        room = serializer.save(host=self.request.user, visibility=visibility)
        # Notify clients of the new room creation
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
        user = request.user
        if request.user.is_authenticated:
            # Authenticated user joins the room
            participant, created = Participant.objects.get_or_create(user=request.user, room=room)
            create_room_notification(user, room)
        else:
            # Anonymous user joins the room, generate a unique anonymous_user_id
            anonymous_user_id = request.session.get('anonymous_user_id')
            if not anonymous_user_id:
                anonymous_user_id = str(uuid4())
                request.session['anonymous_user_id'] = anonymous_user_id
            
            participant, created = Participant.objects.get_or_create(anonymous_user_id=anonymous_user_id, room=room)

        if created:
            # Notify others in the room about the new participant
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'video_chat_{room.id}',
                {
                    'type': 'user_joined',
                    'message': f'User {request.user.username if request.user.is_authenticated else "Anonymous"} has joined the room.'
                }
            )

        return Response({'message': 'Joined room successfully'}, status=status.HTTP_200_OK)
    

    @action(detail=True, methods=['get'], url_path='participant')
    def get_participants(self, request, pk=None):
        print("i'm here")
        # Fetch the room by ID (pk)
        try:
            room_id = request.data.get('id')
            print(room_id)
        except Room.DoesNotExist:
            return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)

        # Get all participants (authenticated and anonymous) for the room
        participants = Participant.objects.filter(room=room_id)
        serializer = ParticipantSerializer(participants, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


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


def create_room_notification(user, room):
    Notification.objects.create(
        user=user,
        message=f'You have joined room {room.title}',
        notification_type='room_event'
    )

# Attendee View
class AttendeeView(APIView):
    permission_classes = [IsAuthenticated]

    """
    View for adding a user as an attendee to a room.
    If the user is already an attendee, it returns an appropriate message.
    """
    def post(self, request, room_id):
        room = get_object_or_404(Room, id=room_id)
        user = request.user
        
        # Check if the user is already an attendee of the room
        if Attendee.objects.filter(user=user, room=room).exists():
            # If user is already a member, return the room data with a message
            return Response(
                {'detail': 'Already a member of this room.', 'room': RoomSerializer(room).data},
                status=status.HTTP_200_OK
            )

        # If the user is not an attendee, create a new attendee entry
        data = {'user': user.id, 'room': room.id, 'is_interested': True}
        serializer = AttendeeSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Calendar Event View
class CalendarEventView(APIView):
    permission_classes = [IsAuthenticated]

    """
    View for adding a room event to the user's calendar
    """
    def post(self, request, room_id):
        """
        Add a room event to the user's calendar.
        """
        room = get_object_or_404(Room, id=room_id)
        user = request.user
        
        data = {'user': user.id, 'room': room.id}
        serializer = CalendarEventSerializer(data=data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        """
        Retrieve all calendar events for the logged-in user.
        """
        user = request.user
        events = CalendarEvent.objects.filter(user=user)
        serializer = CalendarEventSerializer(events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


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


class ActivityViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='like')
    def like(self, request):
        return self._handle_activity(request, Activity.LIKE)

    @action(detail=False, methods=['post'], url_path='unlike')
    def unlike(self, request):
        return self._handle_activity(request, Activity.UNLIKE)

    @action(detail=False, methods=['post'], url_path='follow')
    def follow(self, request):
        return self._handle_activity(request, Activity.FOLLOW)

    @action(detail=False, methods=['post'], url_path='unfollow')
    def unfollow(self, request):
        return self._handle_activity(request, Activity.UNFOLLOW)
    

    def _handle_activity(self, request, activity_type):
        user = request.user
        object_id = request.data.get('object_id')
        object_type = request.data.get('object_type')  # 'post', 'comment', or 'topic'

        try:
            content_type = ContentType.objects.get(model=object_type)
            model_class = content_type.model_class()
            obj = model_class.objects.get(id=object_id)
        except ContentType.DoesNotExist:
            return Response({"error": "Invalid object type"}, status=status.HTTP_400_BAD_REQUEST)
        except model_class.DoesNotExist:
            return Response({"error": f"{object_type.capitalize()} not found"}, status=status.HTTP_404_NOT_FOUND)

        # Check if the user already has this activity
        activity_exists = Activity.objects.filter(
            user=user, content_type=content_type, object_id=obj.id, activity_type=activity_type
        ).exists()

        if activity_exists:
            # Remove activity
            Activity.objects.filter(user=user, content_type=content_type, object_id=obj.id, activity_type=activity_type).delete()
            message = f"You have removed your {activity_type.lower()} for this {object_type}"
        else:
            # Create activity
            Activity.objects.create(user=user, content_type=content_type, object_id=obj.id, activity_type=activity_type)
            message = f"You have successfully {activity_type.lower()}d this {object_type}"

        # Serialize and return the full post in the response for both comments and posts
        if object_type == 'comment':
            post = obj.post  # Get the post related to the comment
        elif object_type == 'post':
            post = obj  # Directly get the post

        if object_type in ['comment', 'post']:
            # Serialize the post and return in response
            serialized_post = PostSerializer(post, context={'request': request}).data
            return Response({"message": message, "post": serialized_post}, status=status.HTTP_201_CREATED)
        

        Notification.objects.create(
            user=self.request.user,
            message=f'New activity created: {object_type}.',
            notification_type='activity_event'
        )
        return Response({"message": message}, status=status.HTTP_201_CREATED)



    def _serialize_object(self, obj, object_type):
        """
        Serialize the object based on its type (post, comment, topic, etc.).
        """
        if object_type == 'post':
            return PostSerializer(obj).data
        elif object_type == 'comment':
            return CommentSerializer(obj).data
        elif object_type == 'topic':
            return TopicSerializer(obj).data
        else:
            return None


    # def _handle_activity(self, request, activity_type):
    #     user = request.user
    #     object_id = request.data.get('object_id')
    #     object_type = request.data.get('object_type')  # 'post', 'comment', or 'topic'

    #     try:
    #         content_type = ContentType.objects.get(model=object_type)
    #         model_class = content_type.model_class()
    #         obj = model_class.objects.get(id=object_id)
    #     except ContentType.DoesNotExist:
    #         return Response({"error": "Invalid object type"}, status=status.HTTP_400_BAD_REQUEST)
    #     except model_class.DoesNotExist:
    #         return Response({"error": f"{object_type.capitalize()} not found"}, status=status.HTTP_404_NOT_FOUND)

    #     # Check if the user already has this activity
    #     if Activity.objects.filter(user=user, content_type=content_type, object_id=obj.id, activity_type=activity_type).exists():
    #         # Remove activity
    #         Activity.objects.filter(user=user, content_type=content_type, object_id=obj.id, activity_type=activity_type).delete()
    #         return Response({"message": f"You have removed your {activity_type.lower()} for this {object_type}"}, status=status.HTTP_200_OK)
        
    #     # Create activity
    #     Activity.objects.create(user=user, content_type=content_type, object_id=obj.id, activity_type=activity_type)
    #     return Response({"message": f"You have successfully {activity_type.lower()}d this {object_type}"}, status=status.HTTP_201_CREATED)

class DashboardViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard(self, request):
        user = request.user

        # Fetch all valid visibility levels from the database
        visibility_levels = list(Visibility.objects.values_list('id', flat=True))

        # Determine visibility from query params or user profile, else pick a random level
        visibility = (
            request.query_params.get('visibility') 
            or getattr(user, 'visibility', None)
        )
        visibility = visibility if visibility in visibility_levels else random.choice(visibility_levels)

        # Fetch user interests to avoid redundant queries
        user_interests = user.interests.values_list('id', flat=True)

        # Helper function to fetch and ensure minimum item count
        def fetch_with_minimum(queryset, min_count=5):
            items = list(queryset.distinct())
            if len(items) < min_count:
                additional_items = queryset.model.objects.filter(
                    visibility__in=visibility_levels
                ).exclude(id__in=[item.id for item in items]).order_by('?')[:min_count - len(items)]
                items.extend(additional_items)
            return items

        # Fetch rooms, forums, and posts with the dynamic visibility filter
        rooms = fetch_with_minimum(
            Room.objects.filter(
                is_active=True, visibility=visibility, tags__in=user_interests
            )
        )
        forums = fetch_with_minimum(
            Forum.objects.filter(
                visibility=visibility, interests__in=user_interests
            )
        )
        posts = fetch_with_minimum(
            Post.objects.filter(
                visibility=visibility, tags__in=user_interests
            )
        )

        # Fetch recent activities for the user
        activities = Activity.objects.filter(user=user).order_by('-created_at')

        # Serialize the fetched data
        room_serializer = RoomSerializer(rooms, many=True)
        forum_serializer = ForumSerializer(forums, many=True)
        post_serializer = PostSerializer(posts, many=True)
        activity_serializer = ActivitySerializer(activities, many=True)

        return Response(
            {
                'rooms': room_serializer.data,
                'forums': forum_serializer.data,
                'posts': post_serializer.data,
                'activities': activity_serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    


class ForumViewSet(viewsets.ModelViewSet):
    # queryset = Forum.objects.all()
    # serializer_class = ForumSerializer

    queryset = Forum.objects.prefetch_related('members').all()  # prefetch members to optimize query
    serializer_class = ForumSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def follow(self, request, pk=None):
        forum = self.get_object()
        user = request.user

        # Check if the user is already following the forum
        if ForumFollow.objects.filter(forum=forum, user=user).exists():
            return Response({"detail": "Already following this forum"}, status=status.HTTP_400_BAD_REQUEST)

        # Create a follow relationship
        ForumFollow.objects.create(forum=forum, user=user)
        return Response({"detail": "You are now following this forum"}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def unfollow(self, request, pk=None):
        forum = self.get_object()
        user = request.user

        # Check if the user is following the forum
        follow_instance = ForumFollow.objects.filter(forum=forum, user=user).first()
        if not follow_instance:
            return Response({"detail": "You are not following this forum"}, status=status.HTTP_400_BAD_REQUEST)

        # Remove the follow relationship
        follow_instance.delete()
        return Response({"detail": "You have unfollowed this forum"}, status=status.HTTP_204_NO_CONTENT)

class ForumPostViewSet(viewsets.ModelViewSet):
    queryset = ForumPost.objects.all()
    serializer_class = ForumPostSerializer

    def perform_create(self, serializer):
        """
        Custom behavior for creating a new post. Only users who are members of the forum
        can create posts in that forum.
        """
        forum = get_object_or_404(Forum, id=self.request.data.get('forum'))

        # Check if the user is part of the forum
        if not ForumFollow.objects.filter(user_id=self.request.user.id, forum=forum).exists():
            raise PermissionDenied("You must be a member of this forum to create a post.")
        
        # Create a notification for the new post
        Notification.objects.create(
            user=self.request.user,
            message=f'New post in forum: {forum.name}.',
            notification_type='forum_post_event'
        )
        
        # Save the post with the current user and forum
        serializer.save(user=self.request.user, forum=forum)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a specific forum post by its ID and ensure the user is part of the forum.
        """
        forumpost_id = request.query_params.get('forumpost_id')
        forum_id = request.query_params.get('forum_id')

        if not forumpost_id:
            return Response({"error": "forumpost_id is required."}, status=400)
        
        if not forum_id:
            return Response({"error": "forum_id is required."}, status=400)

        # Get the forum post
        forum_post = get_object_or_404(ForumPost, id=forumpost_id)

        # Check if the user is a member of the forum
        # if not ForumFollow.objects.filter(user_id=request.user.id, forum=forum_id).exists():
        #     raise PermissionDenied("You must be a member of this forum to view posts.")

        # Serialize the forum post (since it's a single object, we don't use `many=True`)
        serializer = self.get_serializer(forum_post)
        
        return Response(serializer.data)


    
    def list(self, request, *args, **kwargs):
        """
        List all posts for a specific forum using forum_id passed in the query parameters.
        """
        forum_id = request.query_params.get('forum_id')

        if not forum_id:
            return Response({"error": "forum_id is required."}, status=400)

        # Get the forum and check if the user is a member
        forum = get_object_or_404(Forum, id=forum_id)
        # if not ForumFollow.objects.filter(user_id=request.user.id, forum=forum).exists():
        #     raise PermissionDenied("You must be a member of this forum to view posts.")

        # Filter posts by the forum
        posts = ForumPost.objects.filter(forum=forum)

        # Serialize the posts and return the response
        serializer = self.get_serializer(posts, many=True)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """
        Custom update behavior. Allow users to update their own posts.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Check if the user is the author of the post
        if instance.user != request.user:
            raise PermissionDenied("You do not have permission to edit this post.")

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        Custom delete behavior. Allow users to delete their own posts.
        """
        instance = self.get_object()

        # Check if the user is the author of the post
        if instance.user != request.user:
            raise PermissionDenied("You do not have permission to delete this post.")

        self.perform_destroy(instance)
        return Response(status=204)


class ForumCommentViewSet(viewsets.ModelViewSet):
    queryset = ForumComment.objects.all()
    serializer_class = ForumCommentSerializer

    def perform_create(self, serializer):
        post = ForumPost.objects.get(id=self.request.data.get('post'))
        forum = post.forum  # Retrieve the forum from the post
        
        # Check if the user follows the forum through the ForumFollow model
        if not ForumFollow.objects.filter(forum=forum, user=self.request.user).exists():
            raise PermissionDenied("You must be a member of this forum to comment on a post.")
        
        parent = ForumComment.objects.get(id=self.request.data.get('parent')) if self.request.data.get('parent') else None
        Notification.objects.create(
            user=self.request.user,
            message=f'New comment on post: {post.title}.',
            notification_type='forum_comment_event'
        )
        serializer.save(user=self.request.user, post=post, parent=parent)


class ForumFollowViewSet(viewsets.ModelViewSet):
    queryset = ForumFollow.objects.all()
    serializer_class = ForumFollowSerializer

    def perform_create(self, serializer):
        forum = Forum.objects.get(id=self.request.data.get('forum'))
        user = self.request.user
        
        # Add the user to the forum's members
        forum.members.add(user)
        forum.save()
        # Create notification for forum follow
        Notification.objects.create(
            user=user,
            message=f'You are now following the forum: {forum.title}.',
            notification_type='forum_follow_event'
        )

        serializer.save(user=user, forum=forum)