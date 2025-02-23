import base64
from django.core.mail import send_mail, EmailMessage
from smtplib import SMTP
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
import json
import random
import uuid
import time
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from rest_framework import viewsets, status
import sendgrid
from sendgrid.helpers.mail import Mail
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
    return f"{random.randint(0, 9999):04d}"

# def send_otp(email, otp):
#     subject = 'Your OTP Code'
#     message = f'Your OTP code is {otp}. It is valid for 10 minutes.'
#     email_from = settings.DEFAULT_FROM_EMAIL
#     recipient_list = [email]
#     send_mail(subject, message, email_from, recipient_list)

# def send_otp(email, otp):
#     subject = 'Your OTP Code'
#     message = f'Your OTP code is {otp}. It is valid for 10 minutes.'
#     from_email = 'test@bluecampus.com'
#     recipient_list = [email]

#     try:
#         # Directly use SMTP settings to send email
#         email_message = EmailMessage(
#             subject=subject,
#             body=message,
#             from_email=from_email,
#             to=recipient_list,
#         )
#         email_message.send(fail_silently=False, auth_user='apikey', auth_password='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', connection=SMTP(
#             host='smtp.sendgrid.net',
#             port=587,
#             local_hostname=None,
#             timeout=None,
#             source_address=None))
#         print('OTP email sent successfully.')
#     except Exception as e:
#         print(f'Error sending OTP email: {e}')


def send_reset_otp(email, otp):
    print("otp:", otp)
    subject = 'Your Password Reset OTP Code'
    message = (
        f'You have requested to change your password on the BlueCampus app. '
        f'Your OTP code is {otp}. It is valid for 10 minutes. Enter the OTP to change your password.'
    )

    sg = sendgrid.SendGridAPIClient(api_key="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")
    from_email = 'test@bluecampus.com'
    to_email = email

    email_message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=subject,
        plain_text_content=message
    )

    try:
        response = sg.send(email_message)
        if response.status_code == 202:  # 202 indicates the email was accepted for delivery
            print('Reset OTP email sent successfully.')
            return True
        else:
            print(f'Failed to send OTP email: {response.status_code}')
            return False
    except Exception as e:
        print(f'Error sending OTP email: {e}')
        return False

# def send_reset_otp(email, otp):
#     print("otp:", otp)
#     subject = 'Your Password reset OTP Code'
#     message = f'You have requested to change your password on the BlueCampus app. Your OTP code is {otp}. It is valid for 10 minutes. Enter the OTP to change your password.'
#     from_email = 'test@bluecampus.com'
#     recipient_list = [email]

#     try:
#         email_message = EmailMessage(
#             subject=subject,
#             body=message,
#             from_email=from_email,
#             to=recipient_list,
#         )
#         email_message.send(fail_silently=False)
#         print('Reset OTP email sent successfully.')
#         return True
#     except Exception as e:
#         print(f'Error sending OTP email: {e}')
#         return False

# def send_otp(email, otp):
#     print("otp:", otp)
#     subject = 'Your OTP Code'
#     message = f'Your OTP code is {otp}. It is valid for 10 minutes.'
#     from_email = 'test@bluecampus.com'
#     recipient_list = [email]

#     try:
#         email_message = EmailMessage(
#             subject=subject,
#             body=message,
#             from_email=from_email,
#             to=recipient_list,
#         )
#         email_message.send(fail_silently=False)
#         print('OTP email sent successfully.')
#         return True
#     except Exception as e:
#         print(f'Error sending OTP email: {e}')
#         return False

def send_otp(email, otp):
    print("otp:", otp)
    subject = 'Your OTP Code'
    message = f'Your OTP code is {otp}. It is valid for 10 minutes.'

    sg = sendgrid.SendGridAPIClient(api_key="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")
    from_email = 'test@bluecampus.com'
    to_email = email

    email_message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=subject,
        plain_text_content=message
    )

    try:
        response = sg.send(email_message)
        if response.status_code == 202:  # 202 indicates the email was accepted for delivery
            print('OTP email sent successfully.')
            return True
        else:
            print(f'Failed to send OTP email: {response.status_code}')
            return False
    except Exception as e:
        print(f'Error sending OTP email: {e}')
        return False


def set_otp(user):
    otp = generate_otp()
    print(otp)
    user.otp = otp
    user.otp_created_at = timezone.now()
    user.save()

    email_sent = send_otp(user.email, otp)

    if not email_sent:
        return Response({'error': 'Failed to send OTP email. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return True  # Indicate that the OTP was set and sent successfully


def set_reset_otp(user):
    otp = generate_otp()
    print(otp)
    user.reset_otp = otp
    user.otp_created_at = timezone.now()
    user.save()

    email_sent = send_reset_otp(user.email, otp)

    if not email_sent:
        return Response({'error': 'Failed to send OTP email. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return True  # Indicate that the OTP was set and sent successfully

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
