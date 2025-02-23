from django.utils import timezone
from django.db import models
from django.contrib.auth import get_user_model
from bluecampus.app.users.models import Interest
from django.contrib.contenttypes.fields import GenericForeignKey,GenericRelation
from django.contrib.contenttypes.models import ContentType
# from bluecampus.app.feed.models import Visibility


User = get_user_model()



class Activity(models.Model):
    LIKE = 'L'
    FOLLOW = 'F'
    UNLIKE = 'UL'
    UNFOLLOW = 'UF'
    ACTIVITY_TYPE_CHOICES = [
        (LIKE, 'Like'),
        (FOLLOW, 'Follow'),
        (UNLIKE, 'Unlike'),
        (UNFOLLOW, 'Unfollow'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    activity_type = models.CharField(max_length=2, choices=ACTIVITY_TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'content_type', 'object_id', 'activity_type')

    def __str__(self):
        return f"{self.user} {self.get_activity_type_display()} {self.content_object}"
    


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
    visibility = models.ForeignKey('feed.Visibility', on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    scheduled_at = models.DateTimeField(blank=True, null=True)
    tags = models.ManyToManyField(Interest, related_name='rooms', blank=True)
    cover_image = models.ImageField(upload_to='room_covers/', blank=True, null=True)
    max_participants = models.PositiveIntegerField(default=100)
    duration = models.PositiveIntegerField(default=100)
    end_time = models.DateTimeField(blank=True, null=True)
    
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'room')
        constraints = [
            models.UniqueConstraint(fields=['anonymous_user_id', 'room'], name='unique_anonymous_user_in_room')
        ]

    def __str__(self):
        if self.user:
            return f'{self.user.username} in {self.room.title}'
        else:
            return f'{self.anonymous_user_id} in {self.room.title}'

    # def __str__(self):
    #     return f'{self.user.username} in {self.room.title}'


class Attendee(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='attendees')
    is_interested = models.BooleanField(default=True)
    added_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'room')

    def __str__(self):
        return f"{self.user.username} is interested in {self.room.title}"

    @classmethod
    def add_attendee(cls, user, room):
        attendee, created = cls.objects.get_or_create(user=user, room=room)
        return attendee


### New CalendarEvent Model

class CalendarEvent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calendar_events')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='calendar_events')
    event_title = models.CharField(max_length=255)
    event_description = models.TextField(blank=True, null=True)
    event_start = models.DateTimeField()
    event_end = models.DateTimeField()
    added_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Event '{self.event_title}' in {self.room.title} for {self.user.username}"

    @classmethod
    def add_event_to_calendar(cls, user, room):
        event_start = room.scheduled_at
        event_end = room.end_time or (event_start + timezone.timedelta(minutes=room.duration))

        event = cls.objects.create(
            user=user,
            room=room,
            event_title=room.title,
            event_description=room.description,
            event_start=event_start,
            event_end=event_end
        )
        return event

class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f'Message by {self.user.username} in {self.room.title}'

class Recording(models.Model):
    room = models.OneToOneField(Room, on_delete=models.CASCADE)
    audio_file = models.FileField(upload_to='recordings/')
    duration = models.DurationField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
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
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'message', 'reaction_type')

    def __str__(self):
        return f'{self.reaction_type} by {self.user.username} on {self.message.id}'


class Forum(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    interests = models.ManyToManyField(Interest, related_name='forums')
    visibility = models.ForeignKey('feed.Visibility', on_delete=models.SET_NULL, null=True, blank=True)
    rules = models.TextField(blank=True, null=True)
    banner = models.ImageField(upload_to='forum_banner/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    members = models.ManyToManyField(User, related_name='forum_memberships', blank=True)

    def __str__(self):
        return self.name



class ForumPost(models.Model):
    forum = models.ForeignKey(Forum, related_name='forumposts', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class ForumComment(models.Model):
    post = models.ForeignKey(ForumPost, related_name='forumcomments', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', related_name='replies', null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return f'Comment by {self.user.username}'

class ForumFollow(models.Model):
    forum = models.ForeignKey(Forum, related_name='followers', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} follows {self.forum.name}'