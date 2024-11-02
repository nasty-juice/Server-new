# myapp/storages.py
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os

class PrivateMediaStorage(FileSystemStorage):
    def __init__(self, *args, **kwargs):
        # settings.BASE_DIR을 기준으로 private_media 경로 지정
        # kwargs['location'] = os.path.join(settings.BASE_DIR, 'private_media')
        kwargs['location'] = os.path.join(settings.BASE_DIR, 'private_media')
        super().__init__(*args, **kwargs)
