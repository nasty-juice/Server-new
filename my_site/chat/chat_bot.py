from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .utils import encrypt_message
import os
import django

def chat_open_message(chat_room):
    from .models import ChatMessage
    location = chat_room.name.split("_")[0]
    open_message = f"{location} 채팅방이 열렸습니다."
    
    ChatMessage.objects.create(
        chat_room = chat_room, 
        message = encrypt_message(open_message), 
        user = None,
        is_system = True
    )
    return open_message

@shared_task
def chat_send_time_message(group_name, message="hello"):
    # Django 설정 초기화
    print(f'group_name : {group_name}')
    channel_layer = get_channel_layer()
    print(f'channel_layer : {channel_layer}')
    try:
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "send_to_group",
                "status" : "SYSTEM",
                "message": message,
            }
        )
        print("전송 되었습니다.")
    except Exception as e:
        print(f"메시지 전송 실패: {e}")