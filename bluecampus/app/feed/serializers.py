from rest_framework import serializers
from .models import Topic, Post, Comment,PostAttachment 
import json
from django.core import serializers as sz

class TopicSerializer(serializers.ModelSerializer):
    followers_count = serializers.SerializerMethodField()

    class Meta:
        model = Topic
        fields = "__all__"

    def get_followers_count(self, obj):
        return obj.followings.count()

class PostAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostAttachment
        fields = ['id', 'attachment', 'uploaded_at']

class PostSerializer(serializers.ModelSerializer):
    likes_count = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    
    topic_details = serializers.SerializerMethodField()
    # topic=TopicSerializer(write_only=True,many=False)
    topic = serializers.PrimaryKeyRelatedField(queryset=Topic.objects.all())
    files = PostAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = "__all__"
        read_only_fields = ['user', 'comment_count', 'created_at', 'likes']

    def get_likes_count(self, obj):
        return obj.likes.count()
    
    def get_comments(self, obj):
        comments=Comment.objects.filter(post=obj)
        obj.comment_count=len(comments)
        obj.save()
        # json_data=json.dumps(comments)
        # data = sz.serialize('json', comments)
        # print(list(comments))
        return CommentSerializer(comments,many=True).data
    
    def get_topic_details(self, obj):
        return {"id":obj.topic.id,"title":obj.topic.title}

class CommentSerializer(serializers.ModelSerializer):
    replies = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    post=PostSerializer(write_only=True,many=False)
    class Meta:
        model = Comment
        fields = "__all__"
    
    def get_likes_count(self, obj):
        return obj.likes.count()
    
    def get_replies(self, obj):
        return CommentSerializer(obj.replies.all(), many=True).data


