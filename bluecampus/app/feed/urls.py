from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationSettingsView, NotificationViewSet, TopicViewSet, PostViewSet, CommentViewSet, PostCommentCountViewSet, VisibilityViewSet

router = DefaultRouter()
router.register(r'topic', TopicViewSet)
router.register(r'visibility', VisibilityViewSet)
router.register(r'post', PostViewSet)
router.register(r'comment', CommentViewSet)
router.register(r'post-comment-count', PostCommentCountViewSet, basename='post-comment-count')
router.register(r'notifications', NotificationViewSet, basename='notifications')

urlpatterns = [
    path('', include(router.urls)),
    path('notification-settings/', NotificationSettingsView.as_view(), name='notification-settings'),

    # path('activity/', create_activity),
    # path('feed/', view_feed),
]
