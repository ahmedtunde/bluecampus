from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RoomViewSet, ForumViewSet, ActivityViewSet, DashboardViewSet

router = DefaultRouter()
router.register(r'rooms', RoomViewSet)
router.register(r'forums', ForumViewSet)
router.register(r'activities', ActivityViewSet)
router.register(r'dashboard', DashboardViewSet, basename='dashboard')

urlpatterns = [
    path('', include(router.urls)),
]
