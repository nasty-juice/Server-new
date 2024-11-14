from django.dispatch import receiver
from django.conf import settings
from django.db.models.signals import post_delete

from allauth.account.signals import email_confirmed

from .models import CustomUser

import os

@receiver(email_confirmed)
def update_email_verified_status(sender, request, email_address, **kwargs):
    # Fetch the CustomUser instance associated with this email
    user = CustomUser.objects.get(email=email_address.email)
    
    # Update the email_verified field to True
    user.email_verified = True
    user.save()
    
@receiver(post_delete, sender=CustomUser)
def delete_user_image(sender, instance, **kwargs):
    # 사용자 이미지가 있을 경우 삭제
    if instance.student_card_image:
        try:
            # 이미지 파일 경로 가져오기
            image_path = instance.student_card_image.path
            if os.path.isfile(image_path):
                os.remove(image_path)
        except Exception as e:
            # 예외 발생 시 로그를 남기거나 오류 처리
            print(f"Error deleting image: {e}")