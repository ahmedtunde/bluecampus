from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from ..activity.models import Activity
from ..users.models import Interest

User = get_user_model()

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    notification_type = models.CharField(max_length=100, choices=[
        ('room_event', 'Room Event'),
        ('user_event', 'User Event'),
        ('system', 'System Message')
    ])  # Example of notification types

    def __str__(self):
        return f'Notification for {self.user.username} - {self.message[:20]}'

def upload_to(instance, filename):
    return f'post_files/{instance.post.id}/{filename}'





class NotificationSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_settings')

    # Email Notifications
    email_class_start = models.BooleanField(default=True)
    email_new_follower = models.BooleanField(default=True)
    email_new_badge = models.BooleanField(default=True)

    # Push Notifications
    push_class_start = models.BooleanField(default=True)
    push_new_follower = models.BooleanField(default=True)
    push_new_badge = models.BooleanField(default=True)

    def __str__(self):
        return f"Notification settings for {self.user.username}"
    


class Topic(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    followings = GenericRelation(Activity)

    def __str__(self):
        return self.title
    
    def followers_count(self):
        return self.followings.count()

class Visibility(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    @classmethod
    def get_default(cls):
        """Returns the default visibility level, or the first one available."""
        return cls.objects.first()  # Or apply specific logic as needed

    class Meta:
        verbose_name_plural = "Visibility Levels"

class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True)  # Updated `on_delete` behavior and added `blank=True`
    comment_count = models.PositiveIntegerField(default=0)
    tags = models.ManyToManyField(Interest, related_name='posts', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    visibility = models.ForeignKey(Visibility, on_delete=models.SET_NULL, null=True, blank=True)
    likes = GenericRelation(Activity, related_query_name='post')  # Added `related_query_name`

    class Meta:
        verbose_name = "Post"  # Added verbose name for readability
        verbose_name_plural = "Posts"

    def __str__(self):
        return self.title

class PostAttachment(models.Model):
    post = models.ForeignKey(Post, related_name='attachments', on_delete=models.CASCADE)
    attachment = attachment = models.FileField(upload_to='post_upload/', null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Post Attachment"
        verbose_name_plural = "Post Attachments"

    def __str__(self):
        return f"{self.post.title} - {self.attachment.name if self.attachment else 'No Attachment'}"
    



class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    likes = GenericRelation(Activity)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='replies', on_delete=models.CASCADE)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.post.title}"
