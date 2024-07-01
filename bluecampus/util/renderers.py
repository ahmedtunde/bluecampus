import base64
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
import json
import random
import uuid
import time
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

# def generate_otp():
#     return str(random.randint(100000, 999999))

# def set_otp(user):
#     otp = generate_otp()
#     user.otp = otp
#     user.otp_created_at = timezone.now()
#     user.save()
#     send_mail(
#         'Your OTP Code',
#         f'Your OTP code is {otp}',
#         'noreply@example.com',
#         [user.email],
#         fail_silently=False,
#     )

def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp(email, otp):
    subject = 'Your OTP Code'
    message = f'Your OTP code is {otp}. It is valid for 10 minutes.'
    email_from = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email]
    send_mail(subject, message, email_from, recipient_list)

def set_otp(user):
    otp = generate_otp()
    user.otp = otp
    user.otp_created_at = timezone.now()
    user.save()
    send_otp(user.email, otp)

# def send_otp_email(email, otp):
#     subject = 'Your OTP Code'
#     message = f'Your OTP code is {otp}'
#     send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])


class ResponseRenderer(JSONRenderer):
  charset = 'utf-8'
  
  def render(self, data, accepted_media_type=None, renderer_context=None):
    response = ''
    
    if 'ErrorDetail' in str(data):
      response = json.dumps({ 'error': data })
    else:
      response = json.dumps({ 'data': data })
    return response  
  
def format_response(**kwargs):
    ''' Helper function to format response '''
    if kwargs.get('error'):
        return Response({'error': kwargs.get('error'), **kwargs},
                        status=kwargs.get('status', 400))
    return Response({**kwargs}, status=kwargs.get('status', 200))

# def generate_glcode(prefix="GL"):
    # unique_id = str(uuid.uuid4().hex)[:6]  # Generate a unique 6-character ID
    # glcode = f"{prefix}-{unique_id}"
    # return glcode
user_counter = {}  # Keeps track of the counter for each user


def generate_transaction_code(user_id, prefix="TNX"):
    if user_id not in user_counter:
        user_counter[user_id] = 1
    else:
        user_counter[user_id] += 1
    tnx_id = f"{prefix}_{user_counter[user_id]:04d}"
    return tnx_id

def generate_gl_code(user_id, prefix="GL"):
    if user_id not in user_counter:
        user_counter[user_id] = 1
    else:
        user_counter[user_id] += 1
    gl_code = f"{prefix}_{user_counter[user_id]:04d}"
    return gl_code

def calculate_group_balance(transaction_types):
    balance = 0.0
    for transaction_type, transactions in transaction_types.items():
        for transaction in transactions:
            balance += float(transaction['amount'])
    return balance

def generate_12_digit_uuid():
    # Generate a random 10-digit number
    random_number = random.randint(1000000000, 9999999999)

    # Get the current timestamp (seconds since epoch)
    timestamp = int(time.time())

    # Combine the random number and timestamp to create a 12-digit identifier
    identifier = f"{random_number:010d}{timestamp:02d}"

    return identifier

def generate_14_digit_uuid():
    # Generate a random 10-digit number
    random_number = random.randint(100000000000, 999999999999)
    # Get the current timestamp (seconds since epoch)
    timestamp = int(time.time())

    # Combine the random number and timestamp to create a 12-digit identifier
    identifier = f"{random_number:012d}{timestamp:02d}"

    return identifier

def double_base64_decode(encoded_value):
    decoded_value = base64.b64decode(encoded_value).decode('utf-8')
    return base64.b64decode(decoded_value).decode('utf-8')
