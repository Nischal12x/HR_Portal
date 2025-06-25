import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HR_Portal.settings')  # <--- USE YOUR REAL PROJECT NAME

app = Celery('HR_Portal')  # <--- USE YOUR REAL PROJECT NAME
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
