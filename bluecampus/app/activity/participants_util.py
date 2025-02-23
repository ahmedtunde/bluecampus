import uuid
import itertools
from bluecampus.app.activity.models import Participant

# Initialize an iterator for anonymous users
anonymous_user_counter = itertools.count(1)  # Initialize a counter for anonymous users

def generate_unique_id():
    """
    Generate a unique ID for users.
    """
    return uuid.uuid4().hex[:8]  # Shorten UUID for simplicity

def generate_unique_username():
    """
    Generate a unique username for anonymous users.
    """
    return f'AnonymousUser_{generate_unique_id()}'

def create_or_update_participant(user, room_id):
    """
    Create or update a participant in the room.

    :param user: The user object or AnonymousUser instance
    :param room_id: The room ID where the participant is joining
    :return: Tuple of (participant, created) where created is a boolean indicating if a new participant was created
    """
    try:
        if isinstance(user, AnonymousUser):
            # Handle anonymous user case
            anonymous_user_id = f'anonymous_{generate_unique_id()}'
            participant, created = Participant.objects.get_or_create(
                anonymous_user_id=anonymous_user_id,
                room_id=room_id,
                defaults={'role': 'listener'}
            )
        else:
            # Handle authenticated user case
            participant, created = Participant.objects.get_or_create(
                user=user,
                room_id=room_id,
                defaults={'role': 'listener'}
            )

        return participant, created

    except Exception as e:
        print(f"Error creating or updating participant: {e}")
        return None, False

def create_anonymous_participant(self, room_id):
    """
    Create an anonymous participant in the room.

    :param room_id: The room ID where the anonymous participant is joining
    :return: Tuple of (participant, created) where created is a boolean indicating if a new participant was created
    """
    anonymous_user_id = f'anonymous_{generate_unique_id()}'
    try:
        participant, created = Participant.objects.get_or_create(
            anonymous_user_id=anonymous_user_id,
            room_id=room_id,
            defaults={'role': 'listener'}
        )
    except Exception as e:
        print(f"Error creating anonymous participant: {e}")
        return None, False

    return participant, created

class AnonymousUser:
    def __init__(self):
        self.username = generate_unique_username()  # Generate a unique username for anonymous user
        self.is_authenticated = False

    def __str__(self):
        return self.username
