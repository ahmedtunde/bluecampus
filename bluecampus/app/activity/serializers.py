from rest_framework import serializers

from bluecampus.app.feed.models import Visibility
from .models import Room, Forum, Activity, Attendee, CalendarEvent, ForumComment, ForumFollow, ForumPost
from rest_framework import serializers
from .models import Room, Participant, Message, Recording, Reaction
from ..users.serializers import InterestSerializer, UserProfileSerializer
from ..feed.serializers import VisibilitySerializer

class ParticipantSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()  # Custom method to handle user data
    room = serializers.ReadOnlyField(source='room.title')

    class Meta:
        model = Participant
        fields = '__all__'
        read_only_fields = ['user', 'room', 'joined_at']
        depth = 2

    def get_user(self, obj):
        if obj.otp:
            # Authenticated user: use the detailed serializer
            return UserProfileSerializer(obj).data
        else:
            # Anonymous user: provide default static data
            return {
                "username": obj.anonymous_user_id,
                "name": "obj.anonymous_user_id",
                "profile_picture": "../../../media/profile_pictures/building.png"  # Static profile picture path
            }


class RoomSerializer(serializers.ModelSerializer):
    host = UserProfileSerializer(read_only=True)

    # participants = ParticipantSerializer(many=True, read_only=True)  # Use nested ParticipantSerializer
    participants = serializers.SerializerMethodField()
    attendees = serializers.SerializerMethodField()
    attendees_count = serializers.SerializerMethodField()
    visibility = serializers.StringRelatedField(read_only=True)  # Display the visibility name in response


    class Meta:
        model = Room
        fields = ['id', 'title', 'description', 'visibility', 'host', 'participants', 'tags', 
                  'scheduled_at', 'cover_image', 'max_participants', 'duration', 'attendees_count', 'attendees']
        # fields = '__all__'
        read_only_fields = ['host', 'participants', 'created_at', 'updated_at']
        depth = 2


    
    def get_attendees_count(self, obj):
        # Count both users and anonymous attendees
        return Attendee.objects.filter(room=obj).count()
    
    def get_participants(self, obj):
        # Return the list of user profiles of all participants with a valid user
        participants = Participant.objects.filter(room=obj).exclude(user__isnull=True)
        return UserProfileSerializer([p.user for p in participants], many=True).data

    def get_attendees(self, obj):
        # Return the list of user profiles of all participants with a valid user
        participants = Attendee.objects.filter(room=obj).exclude(user__isnull=True)
        return UserProfileSerializer([p.user for p in participants], many=True).data


# Attendee Serializer
class AttendeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendee
        fields = ['id', 'user', 'room', 'is_interested', 'added_at']
        read_only_fields = ['added_at']

    def create(self, validated_data):
        attendee, created = Attendee.objects.get_or_create(**validated_data)
        return attendee
    

# Calendar Event Serializer
class CalendarEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalendarEvent
        fields = ['id', 'user', 'room', 'event_title', 'event_description', 'event_start', 'event_end', 'added_at']
        read_only_fields = ['added_at', 'event_title', 'event_description', 'event_start', 'event_end']

    def create(self, validated_data):
        room = validated_data['room']
        user = validated_data['user']
        event = CalendarEvent.add_event_to_calendar(user, room)
        return event


class MessageSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Message
        fields = '__all__'
        read_only_fields = ['user', 'room', 'created_at']
        depth = 2
class RecordingSerializer(serializers.ModelSerializer):
    room = serializers.ReadOnlyField(source='room.title')

    class Meta:
        model = Recording
        fields = '__all__'
        read_only_fields = ['room', 'created_at']
        depth = 2
class ReactionSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    message = serializers.ReadOnlyField(source='message.id')

    class Meta:
        model = Reaction
        fields = '__all__'
        read_only_fields = ['user', 'message', 'created_at']
        depth = 2

class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = '__all__'
        depth = 2


class ForumSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    followers_count = serializers.SerializerMethodField()
    posts_count = serializers.SerializerMethodField()
    visibility = VisibilitySerializer(read_only=True)  # Display the visibility name in response
    interests = InterestSerializer(read_only= True)
    members = serializers.SerializerMethodField()  # Fetch members from ForumFollow

    class Meta:
        model = Forum
        fields = ['id', 'user', 'name', 'description', 'interests', 'visibility', 'rules', 'banner', 'created_at', 'updated_at', 'followers_count', 'posts_count', 'members']

    def get_followers_count(self, obj):
        return obj.followers.count()

    def get_posts_count(self, obj):
        return obj.forumposts.count()
    
    def get_members(self, obj):
        # Get all the users following the forum through ForumFollow
        followers = ForumFollow.objects.filter(forum=obj).select_related('user')
        # Serialize the users who are following the forum
        return UserProfileSerializer([follow.user for follow in followers], many=True).data

class ForumCommentSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = ForumComment
        fields = ['id', 'post', 'user', 'content', 'created_at', 'parent', 'replies']

    def get_replies(self, obj):
        # Serialize replies of the comment
        return ForumCommentSerializer(obj.replies.all(), many=True).data


class ForumPostSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    comments_count = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()  # Allow multiple comments to be serialized

    class Meta:
        model = ForumPost
        fields = ['id', 'forum', 'user', 'title', 'content', 'created_at', 'updated_at', 'comments_count', 'comments']

    def get_comments_count(self, obj):
        return obj.forumcomments.count()
    
    def get_comments(self, obj):
        # Fetch all comments related to the ForumPost and serialize them
        comments = obj.forumcomments.all()  # Get all comments
        return ForumCommentSerializer(comments, many=True).data  # Serialize the comments



class ForumFollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForumFollow
        fields = ['id', 'forum', 'user', 'created_at']