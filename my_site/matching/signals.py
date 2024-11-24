# signals.py
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from chat.models import ChatRoom
# from .tasks import delete_chat_room

# @receiver(post_save, sender=ChatRoom)
# def schedule_deletion(sender, instance, created, **kwargs):
#     if created:
#         delete_chat_room.apply_async((instance.name,), countdown=10)  # 10초 후에 삭제 작업 예약