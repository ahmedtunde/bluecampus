from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Comment, Notification, NotificationSettings, Post, Topic, PostAttachment, Visibility
from .serializers import NotificationSerializer, NotificationSettingsSerializer, TopicSerializer, PostSerializer, CommentSerializer, UpdateNotificationSettingsSerializer, VisibilitySerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, permissions

class TopicViewSet(viewsets.ModelViewSet):
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # serializer.save(host=self.request.user)
        serializer.save()  # Remove `host=self.request.user`


    @action(detail=False, methods=['get'], url_path='view_all_topics')
    def view_all_topics(self, request, pk=None):
        topics = Topic.objects.all()
        data = TopicSerializer(topics, many=True).data
        return Response(data, status=status.HTTP_200_OK)

class NotificationSettingsView(generics.RetrieveUpdateAPIView):
    serializer_class = NotificationSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Ensure that the user gets their own notification settings
        obj, created = NotificationSettings.objects.get_or_create(user=self.request.user)
        return obj

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return UpdateNotificationSettingsSerializer
        return NotificationSettingsSerializer



class VisibilityViewSet(viewsets.ModelViewSet):
    queryset = Visibility.objects.all()
    serializer_class = VisibilitySerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # serializer.save(host=self.request.user)
        serializer.save()  # Remove `host=self.request.user`


    @action(detail=False, methods=['get'], url_path='get_visibility')
    def get(self, request, pk=None):
        visibility = Visibility.objects.all()
        data = VisibilitySerializer(visibility, many=True).data
        return Response(data, status=status.HTTP_200_OK)


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Get notifications for the current user only
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

    @action(detail=False, methods=['post'], url_path='mark-as-read')
    def mark_as_read(self, request):
        # Mark specific notifications as read
        notification_ids = request.data.get('notification_ids', [])
        if not notification_ids:
            return Response({'error': 'No notification IDs provided'}, status=status.HTTP_400_BAD_REQUEST)

        notifications = Notification.objects.filter(user=request.user, id__in=notification_ids)
        notifications.update(is_read=True)
        
        return Response({'message': 'Notifications marked as read'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['delete'], url_path='clear')
    def clear_notifications(self, request):
        # Delete all notifications for the user
        Notification.objects.filter(user=request.user).delete()
        return Response({'message': 'Notifications cleared'}, status=status.HTTP_200_OK)


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    # def get_serializer_context(self):
    #     """Ensure that request context is included."""
    #     context = super().get_serializer_context()
    #     print(f"Serializer context: {context}")  # Debug: Check context
    #     return context

    def get_serializer_context(self):
        # Ensure context includes the request for serialization
        return {'request': self.request, 'format': self.format_kwarg, 'view': self}
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'], url_path='post_comment')
    def post_comment(self, request, pk=None):
        user = request.user
        post_id = request.data.get('post_id')
        content = request.data.get('content')
        parent_id = request.data.get('parent_id', None)

        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)

        parent_comment = None
        if parent_id:
            try:
                parent_comment = Comment.objects.get(id=parent_id)
            except Comment.DoesNotExist:
                return Response({"error": "Parent comment not found"}, status=status.HTTP_404_NOT_FOUND)

        comment = Comment.objects.create(user=user, post=post, content=content, parent=parent_comment)
        return Response({"message": "Successfully added comment", "comment": CommentSerializer(comment).data}, status=status.HTTP_201_CREATED)

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        """Ensure context includes the request for serialization."""
        return {'request': self.request, 'format': self.format_kwarg, 'view': self}

    def perform_create(self, serializer):
        """Create a new post and handle file attachments."""
        post = serializer.save(user=self.request.user)
        files = self.request.FILES.getlist('files')
        for file in files:
            try:
                PostAttachment.objects.create(post=post, attachment=file)
            except Exception as e:
                print(f"Error while saving attachment: {e}")

    def get_queryset(self):
        """Override to filter posts by ownership if specified."""
        is_owner = self.request.query_params.get('is_owner', None)
        if is_owner == "true":
            return Post.objects.filter(user=self.request.user)
        return Post.objects.all()

    def list(self, request, *args, **kwargs):
        """List posts with optional filtering."""
        visibility = request.query_params.get('visibility', None)
        queryset = self.get_queryset()

        if visibility:
            queryset = queryset.filter(visibility=visibility)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # serializer = self.get_serializer(queryset, many=True)
        # return Response(serializer.data)
        # serializer = self.get_serializer(queryset, many=True)
        # return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """Retrieve a post by ID including its attachments."""
        queryset = self.get_queryset()
        post = get_object_or_404(queryset, pk=pk)
        serializer = self.get_serializer(post)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """Update an existing post."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Additional handling for attachments update if needed.

        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """Delete a post."""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

# Additional view to get a post's comments count
class PostCommentCountViewSet(viewsets.GenericViewSet):
    @action(detail=True, methods=['get'], url_path='comment-count')
    def get_comment_count(self, request, pk=None):
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response({"comment_count": post.comment_count}, status=status.HTTP_200_OK)
