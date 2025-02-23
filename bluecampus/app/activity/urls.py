from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AttendeeView, CalendarEventView, ForumCommentViewSet, ForumFollowViewSet, ForumPostViewSet, RoomViewSet, ForumViewSet, ActivityViewSet, DashboardViewSet, room_view

router = DefaultRouter()
router.register(r'rooms', RoomViewSet, basename='rooms')
router.register(r'activities', ActivityViewSet, basename='activities')
router.register(r'dashboard', DashboardViewSet, basename='dashboard')
router.register(r'forums', ForumViewSet, basename='forum')
router.register(r'forumposts', ForumPostViewSet, basename='post')
router.register(r'forumcomments', ForumCommentViewSet, basename='comment')
router.register(r'forum-follows', ForumFollowViewSet, basename='forum-follow')

urlpatterns = [
    path('', include(router.urls)),
    path('room/<int:room_id>/', room_view, name='room_view'),
    path('room/<int:room_id>/attend/', AttendeeView.as_view(), name='add-attendee'),
    path('rooms/<int:room_id>/calendar/', CalendarEventView.as_view(), name='add-calendar-event'),
    path('calendar/', CalendarEventView.as_view(), name='list-calendar-events'),

]
