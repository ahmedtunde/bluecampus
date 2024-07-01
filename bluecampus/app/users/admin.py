from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Interest

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('bio', 'otp_verified', 'interests', 'otp', 'otp_created_at')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('bio', 'otp_verified', 'interests', 'otp', 'otp_created_at')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Interest)
