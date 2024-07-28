from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()
from django.contrib.contenttypes.fields import GenericForeignKey,GenericRelation
from django.contrib.contenttypes.models import ContentType
from ..activity.models import Activity
from ..users.models import Interest
class Topic(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    followings = GenericRelation(Activity)


    def __str__(self):
        return self.title
    
    def followers_count(self):
        return self.followings.count()



class Post(models.Model):
    VISIBILITY_CHOICES = [
        ('global', 'Global'),
        ('national', 'National'),
        ('institution', 'Institution'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE,null=True)
    comment_count=models.PositiveIntegerField(default=0)
    tags = models.ManyToManyField(Interest, related_name='posts', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='global')
    likes = GenericRelation(Activity)

  
    # def __str__(self):
    #     return f"{self.user.username} follows {self.topic.name}"
    

class PostAttachment(models.Model):
    post = models.ForeignKey(Post, related_name='files', on_delete=models.CASCADE)
    attachment = models.FileField(upload_to='post_files/',null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.post.title} - {self.attachment.name}"
    
class Comment(models.Model):#for following and unfollowing
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    content=models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    likes = GenericRelation(Activity)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='replies', on_delete=models.CASCADE)

   
    # def __str__(self):
    #     return f"{self.user.username} follows {self.group.name}"

# class Like(models.Model):#for liking and unliking both posts and comments
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
#     object_id = models.PositiveIntegerField()
#     content_object = GenericForeignKey('content_type', 'object_id')
#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         unique_together = ('user', 'content_type', 'object_id')

#     def __str__(self):
#         return f"{self.user.username} likes {self.content_object}"
    