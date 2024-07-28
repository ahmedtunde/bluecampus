from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RoomViewSet, ForumViewSet, ActivityViewSet, DashboardViewSet, room_view

router = DefaultRouter()
router.register(r'rooms', RoomViewSet)
router.register(r'forums', ForumViewSet)
router.register(r'activities', ActivityViewSet)
router.register(r'dashboard', DashboardViewSet, basename='dashboard')

urlpatterns = [
    path('', include(router.urls)),
    path('room/<int:room_id>/', room_view, name='room_view'),

]
