# # signals.py
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from .models import CustomUser
# from .utils import move_to_private_media
# from django.conf import settings
# import os

# @receiver(post_save, sender=CustomUser)
# def post_save_custom_user(sender, instance, **kwargs):
#     if instance.student_card_image:
#         # 이미지 파일이 PRIVATE_MEDIA_ROOT에 이미 있는지 확인
#         current_path = instance.student_card_image.path
#         if settings.PRIVATE_MEDIA_ROOT in current_path:
#             print("이미 파일이 PRIVATE_MEDIA_ROOT에 있습니다.")
#             return  # 파일이 이미 옮겨진 경우 중복 처리 방지

#         # 임시 경로에 파일이 있는 경우에만 이동
#         if os.path.exists(current_path):
#             move_to_private_media(instance, 'student_card_image')
#         else:
#             print("임시 파일 경로를 찾을 수 없습니다.")