from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import create_activity,TopicViewSet,PostViewSet,CommentViewSet,view_feed

router = DefaultRouter()
router.register(r'topic', TopicViewSet)
router.register(r'post', PostViewSet)
router.register(r'comment', CommentViewSet)
urlpatterns = [
    path('', include(router.urls)),
    path('activity', create_activity),
    path('feed', view_feed),
]
