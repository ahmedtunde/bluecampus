from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta

class Interest(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class CustomUser(AbstractUser):
    bio = models.TextField(blank=True, null=True)
    otp_verified = models.BooleanField(default=False)
    interests = models.ManyToManyField(Interest, related_name='users', blank=True)
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    reset_otp = models.CharField(max_length=6, blank=True, null=True)
    deleted_status = models.BooleanField(default=False)
    recovery_email = models.EmailField(null=True, blank=True)  # Field to store the recovery email

    def __str__(self):
        return self.username

    def is_otp_expired(self):
        if self.otp_created_at:
            return timezone.now() > self.otp_created_at + timedelta(minutes=10)
        return True
    
