from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, status
from .models import Room, Participant, Message, Recording, Reaction, Forum, Activity
from .serializers import RoomSerializer, ParticipantSerializer, MessageSerializer, RecordingSerializer, ReactionSerializer, ForumSerializer, ActivitySerializer

class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(host=self.request.user)

    @action(detail=True, methods=['post'], url_path='join')
    def join_room(self, request, pk=None):
        room = self.get_object()
        Participant.objects.create(user=request.user, room=room)
        return Response({'message': 'Joined room successfully'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='leave')
    def leave_room(self, request, pk=None):
        room = self.get_object()
        participant = Participant.objects.filter(user=request.user, room=room).first()
        if participant:
            participant.delete()
            return Response({'message': 'Left room successfully'}, status=status.HTTP_200_OK)
        return Response({'error': 'You are not a participant of this room'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='raise-hand')
    def raise_hand(self, request, pk=None):
        room = self.get_object()
        participant = Participant.objects.filter(user=request.user, room=room).first()
        if participant:
            participant.role = 'speaker'
            participant.save()
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
            return Response({'message': 'Participant accepted as speaker'}, status=status.HTTP_200_OK)
        return Response({'error': 'Participant not found'}, status=status.HTTP_400_BAD_REQUEST)

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


class ForumViewSet(viewsets.ModelViewSet):
    queryset = Forum.objects.all()
    serializer_class = ForumSerializer

class ActivityViewSet(viewsets.ModelViewSet):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer

class DashboardViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard(self, request):
        user = request.user
        visibility = request.query_params.get('visibility', 'global')

        # Fetch suggested rooms and forums based on user interests and visibility
        rooms = Room.objects.filter(interests__in=user.interests.all(), visibility=visibility).distinct()
        forums = Forum.objects.filter(interests__in=user.interests.all(), visibility=visibility).distinct()

        # Fetch activities
        activities = Activity.objects.filter(user=user)

        room_serializer = RoomSerializer(rooms, many=True)
        forum_serializer = ForumSerializer(forums, many=True)
        activity_serializer = ActivitySerializer(activities, many=True)

        return Response({
            'rooms': room_serializer.data,
            'forums': forum_serializer.data,
            'activities': activity_serializer.data
        }, status=status.HTTP_200_OK)
