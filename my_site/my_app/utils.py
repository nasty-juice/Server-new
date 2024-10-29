import os
import shutil
from django.conf import settings

# 유저 객체, 모델 필드 이름, 폴더명
def move_to_private_media(instance, field_name, sub_dir='student_cards'):
    """파일을 PRIVATE_MEDIA_ROOT로 이동하고 경로를 모델 인스턴스에 업데이트"""
    # field_name으로 접근할 필드 확인
    file_field = getattr(instance, field_name, None)
    if file_field and file_field.name:  # 파일 필드가 있고, 파일이 저장된 경우
        temp_path = file_field.path
        # 최종 PRIVATE_MEDIA_ROOT의 하위 폴더 경로
        private_dir = os.path.join(settings.PRIVATE_MEDIA_ROOT, sub_dir)
        os.makedirs(private_dir, exist_ok=True)

        # 원래 파일명을 유지하여 최종 경로 설정
        final_path = os.path.join(private_dir, os.path.basename(temp_path))
        shutil.move(temp_path, final_path)  # 파일 이동

        # 파일 경로를 모델 필드에 업데이트
        file_field.name = os.path.join(sub_dir, os.path.basename(temp_path))
        instance.save(update_fields=[field_name])  # 해당 필드만 업데이트