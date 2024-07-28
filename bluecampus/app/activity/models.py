from django.db import models
from django.contrib.auth import get_user_model
from bluecampus.app.users.models import Interest
from django.contrib.contenttypes.fields import GenericForeignKey,GenericRelation
from django.contrib.contenttypes.models import ContentType
User = get_user_model()

class Room(models.Model):
    VISIBILITY_CHOICES = [
        ('global', 'Global'),
        ('national', 'National'),
        ('institution', 'Institution'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    host = models.ForeignKey(User, related_name='hosted_rooms', on_delete=models.CASCADE)
    participants = models.ManyToManyField(User, through='Participant', related_name='rooms')
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='global')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    scheduled_at = models.DateTimeField(blank=True, null=True)
    tags = models.ManyToManyField(Interest, related_name='rooms', blank=True)
    cover_image = models.ImageField(upload_to='room_covers/', blank=True, null=True)
    max_participants = models.PositiveIntegerField(default=100)

    def __str__(self):
        return self.title

class Participant(models.Model):
    ROLE_CHOICES = [
        ('host', 'Host'),
        ('speaker', 'Speaker'),
        ('listener', 'Listener'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    anonymous_user_id = models.CharField(max_length=255, null=True, blank=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='listener')
    joined_at = models.DateTimeField(auto_now_add=True)

    
    class Meta:
        unique_together = ('user', 'room')
    
    def __str__(self):
        if self.user:
            return  f'{self.user.username} in {self.room.title}'
        else:
            return f'{self.anonymous_user_id} in {self.room.title}'

    # def __str__(self):
    #     return f'{self.user.username} in {self.room.title}'

class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Message by {self.user.username} in {self.room.title}'

class Recording(models.Model):
    room = models.OneToOneField(Room, on_delete=models.CASCADE)
    audio_file = models.FileField(upload_to='recordings/')
    created_at = models.DateTimeField(auto_now_add=True)
    duration = models.DurationField()

    def __str__(self):
        return f'Recording of {self.room.title}'

class Reaction(models.Model):
    REACTION_CHOICES = [
        ('like', 'Like'),
        ('clap', 'Clap'),
        ('heart', 'Heart'),
        ('thumbs_up', 'Thumbs Up'),
        ('thumbs_down', 'Thumbs Down'),
        ('raise_hand', 'Raise Hand'),

    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    reaction_type = models.CharField(max_length=50, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'message', 'reaction_type')

    def __str__(self):
        return f'{self.reaction_type} by {self.user.username} on {self.message.id}'


class Forum(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    visibility = models.CharField(max_length=20, choices=[('global', 'Global'), ('national', 'National'), ('institution', 'Institution')])
    country = models.CharField(max_length=100, blank=True, null=True)
    institution = models.CharField(max_length=100, blank=True, null=True)
    interests = models.ManyToManyField(Interest, related_name='forums')

    def __str__(self):
        return self.name

class Activity(models.Model):
    FOLLOW = 'F'
    LIKE = 'L'
    UP_VOTE = 'U'
    DOWN_VOTE = 'D'
    ACTIVITY_TYPES = (
        (FOLLOW, 'Follow'),
        (LIKE, 'Like'),
        (UP_VOTE, 'Up Vote'),
        (DOWN_VOTE, 'Down Vote'),
    )

    activity_type = models.CharField(max_length=1, choices=ACTIVITY_TYPES,default="L")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE,null=True)
    object_id = models.PositiveIntegerField(null=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return f'{self.user.username} at {self.timestamp}'
