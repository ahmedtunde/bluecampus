from rest_framework import serializers
from .models import Room, Forum, Activity
from rest_framework import serializers
from .models import Room, Participant, Message, Recording, Reaction

class RoomSerializer(serializers.ModelSerializer):
    host = serializers.ReadOnlyField(source='host.username')
    participants = serializers.StringRelatedField(many=True, read_only=True)
    tags = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Room
        fields = '__all__'
        read_only_fields = ['host', 'participants', 'created_at', 'updated_at']

class ParticipantSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    room = serializers.ReadOnlyField(source='room.title')

    class Meta:
        model = Participant
        fields = '__all__'
        read_only_fields = ['user', 'room', 'joined_at']

class MessageSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Message
        fields = '__all__'
        read_only_fields = ['user', 'room', 'created_at']

class RecordingSerializer(serializers.ModelSerializer):
    room = serializers.ReadOnlyField(source='room.title')

    class Meta:
        model = Recording
        fields = '__all__'
        read_only_fields = ['room', 'created_at']

class ReactionSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    message = serializers.ReadOnlyField(source='message.id')

    class Meta:
        model = Reaction
        fields = '__all__'
        read_only_fields = ['user', 'message', 'created_at']

class ForumSerializer(serializers.ModelSerializer):
    class Meta:
        model = Forum
        fields = '__all__'

class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = '__all__'
