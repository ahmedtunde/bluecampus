
from bluecampus.app.activity.models import Participant
from django.core.exceptions import ObjectDoesNotExist
import itertools


# Initialize an iterator for anonymous users
# anonymous_user_counter = itertools.count(start=1)
anonymous_user_counter = itertools.count(1)  # Initialize a counter for anonymous users

def create_or_update_participant(user, room_id):
    print("this is user:", user)
    # if isinstance(user, AnonymousUser):
    #     anonymous_user_id = f'anonymous_{next(anonymous_user_counter)}'
    #     print("here1:", anonymous_user_id)

    #     try:
    #         participant, created = Participant.objects.get_or_create(
    #             anonymous_user_id=anonymous_user_id,
    #             room_id=room_id,
    #             defaults={'role': 'listener'}
    #         )
    #     except Exception as e:
    #         print(f"Error creating or updating participant 1: {e}")
    #         return None, False
    # else:
    try:
        print("here2:",user)

        participant, created = Participant.objects.get_or_create(
            anonymous_user_id=user,
            room_id=room_id,
            defaults={'role': 'listener'}
        )
    except Exception as e:
        print(f"Error creating or updating participant 2: {e}")
        return None, False

    return participant, created

def create_anonymous_participant(user, room_id):
    print(user)
    # Generate a unique anonymous username
    
    anonymous_user_id = f'anonymous_{next(anonymous_user_counter)}'
    print("here1:", anonymous_user_id)

    try:
        participant, created = Participant.objects.get_or_create(
            anonymous_user_id=anonymous_user_id,
            room_id=room_id,
            defaults={'role': 'listener'}
        )
    except Exception as e:
        print(f"Error creating or updating participant 1: {e}")
        return None, False

# Dummy class for anonymous users
class AnonymousUser:
    def __init__(self, username):
        self.username = username
        self.is_authenticated = False

    def __str__(self):
        return self.username
