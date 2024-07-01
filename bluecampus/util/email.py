from django.core.mail import EmailMessage
from django.core.mail import send_mail
from django.conf import settings

class Email:
  @staticmethod
  def send_email(data):
    send_mail(
      data['subject'], 
      data['email_body'], 
      settings.FROM_EMAIL, 
      [data['to_email']], 
      fail_silently=False
    )
    
    

