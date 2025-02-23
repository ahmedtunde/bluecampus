from django.contrib import admin
from .models import NotificationSettings, Topic,Post,PostAttachment
# Register your models here.
admin.site.register(Topic)
admin.site.register(Post)
admin.site.register(PostAttachment)
@admin.register(NotificationSettings)

class NotificationSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'email_class_start', 'email_new_follower', 'email_new_badge', 'push_class_start', 'push_new_follower', 'push_new_badge')