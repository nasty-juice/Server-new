import os
import uuid
from django.conf import settings

def secure_upload_to(instance, filename):
    # SECURE_MEDIA_ROOT 경로가 없다면 생성
    if not os.path.exists(settings.SECURE_MEDIA_ROOT):
        os.makedirs(settings.SECURE_MEDIA_ROOT)
        
    # Generate a unique filename using UUID
    unique_filename = f"{uuid.uuid4().hex}{os.path.splitext(filename)[1]}"
    print(unique_filename)
    
    # SECURE_MEDIA_ROOT 경로 내에 secure 폴더를 생성하여 파일 저장
    return os.path.join(settings.SECURE_MEDIA_ROOT, 'raw', unique_filename)