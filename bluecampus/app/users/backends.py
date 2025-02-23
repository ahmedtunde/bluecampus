from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get('email')
        try:
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            return None

        # Check if the provided password is correct, user is active, and user is not marked as deleted
        if (
            user is not None and  # Ensure user exists
            user.check_password(password) and  # Password is correct
            not user.deleted_status and  # User is not marked as deleted
            self.user_can_authenticate(user)  # User is active and can authenticate
        ):
            return user
        return None

    def get_user(self, user_id):
        try:
            # Ensure we don't return a user marked as deleted
            user = User.objects.get(pk=user_id)
            if user.deleted_status:
                return None
            return user
        except User.DoesNotExist:
            return None