from itertools import count
from rest_framework import serializers
from .models import NotificationSettings, Topic, Post, Comment, PostAttachment, Visibility, Notification
from ..activity.models import Activity, ContentType
from ..users.serializers import UserProfileSerializer

class TopicSerializer(serializers.ModelSerializer):
    followers_count = serializers.SerializerMethodField()

    class Meta:
        model = Topic
        fields = ['id', 'title', 'description', 'followers_count']  # Only include necessary fields

    def get_followers_count(self, obj):
        # Use aggregation to count followers for better performance
        return obj.followings.filter(
            content_type=ContentType.objects.get_for_model(Topic), 
            activity_type=Activity.FOLLOW
        ).count()

class VisibilitySerializer(serializers.ModelSerializer):

    class Meta:
        model = Visibility
        fields = ['id', 'name', 'description']  # Only include necessary fields


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'user', 'message', 'created_at', 'is_read', 'notification_type']
        read_only_fields = ['user', 'created_at']

class NotificationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationSettings
        fields = [
            'email_class_start',
            'email_new_follower',
            'email_new_badge',
            'push_class_start',
            'push_new_follower',
            'push_new_badge',
        ]

class UpdateNotificationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationSettings
        fields = [
            'email_class_start',
            'email_new_follower',
            'email_new_badge',
            'push_class_start',
            'push_new_follower',
            'push_new_badge',
        ]


class PostAttachmentSerializer(serializers.ModelSerializer):
    attachment_url = serializers.SerializerMethodField()

    class Meta:
        model = PostAttachment
        fields = ['id', 'attachment_url', 'uploaded_at']

    def get_attachment_url(self, obj):
        # Add the base URL to the attachment path
        request = self.context.get('request')
        base_url = "https://tuns111.pythonanywhere.com"
        return f"{base_url}{obj.attachment.url}" if obj.attachment else None


class PostSerializer(serializers.ModelSerializer):
    likes_count = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    topic_details = serializers.SerializerMethodField()
    attachments = PostAttachmentSerializer(many=True, read_only=True)
    user = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'title', 'description', 'topic', 'tags', 'created_at', 'visibility', 'attachments', 'topic_details', 'comments', 'likes_count', 'user', 'comment_count']
        read_only_fields = ['user', 'comment_count', 'created_at', 'likes_count', 'attachments']

    def get_likes_count(self, obj):
        # Count the number of likes for the post
        return Activity.objects.filter(
            content_type=ContentType.objects.get_for_model(Post),
            object_id=obj.id,
            activity_type=Activity.LIKE
        ).count()

    def get_comments(self, obj):
        comments = Comment.objects.filter(post=obj)
        return CommentSerializer(comments, many=True, context={'depth': 0}).data


    def get_topic_details(self, obj):
        # Safely access topic details
        if obj.topic:
            return {"id": obj.topic.id, "title": obj.topic.title}
        return None

    def get_user(self, obj):
        # Serialize user profile
        user_serializer = UserProfileSerializer(obj.user, context=self.context)
        return user_serializer.data

    def get_comment_count(self, obj):
        # Count comments directly related to the post
        return obj.comments.count()


class CommentSerializer(serializers.ModelSerializer):
    replies = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = ['id', 'user', 'content', 'created_at', 'parent', 'replies', 'likes_count', 'comment_count']
        read_only_fields = ['user', 'created_at', 'likes_count']

    def get_likes_count(self, obj):
        return Activity.objects.filter(
            content_type=ContentType.objects.get_for_model(Comment),
            object_id=obj.id,
            activity_type=Activity.LIKE
        ).count()

    def get_replies(self, obj):
        # Only include replies if the context includes 'include_replies'
        include_replies = self.context.get('include_replies', False)
        if include_replies:
            return CommentSerializer(obj.replies.all(), many=True, context={'include_replies': False}).data
        return []

    def get_user(self, obj):
        return UserProfileSerializer(obj.user, context=self.context).data

    def get_comment_count(self, obj):
        # Count replies directly related to the comment
        return obj.replies.count()
