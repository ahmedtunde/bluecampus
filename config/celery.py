# celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Create a Celery instance and configure it using the settings from Django.
celery_app = Celery('config')

# Load task modules from all registered Django app configs.
celery_app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps.
celery_app.autodiscover_tasks()

# Schedule the task
celery_app.conf.beat_schedule = {
    'send-payment-reminders': {
        'task':'expense_tracker.app.payments_edves.tasks.send_payment_reminder_emails',
        'schedule': crontab(hour=23, minute=0),  # Adjust the schedule based on your requirements
    },
}