import os
from celery import Celery

# Django의 settings 모듈을 Celery의 기본 설정으로 사용하도록 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'my_site.settings')

app = Celery('matching')

# Django의 settings 모듈에서 설정을 가져오도록 설정
app.config_from_object('django.conf:settings', namespace='CELERY')

# Django 앱에서 task 모듈을 자동으로 찾아서 로드하도록 설정
app.autodiscover_tasks()