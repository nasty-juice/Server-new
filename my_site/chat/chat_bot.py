from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.core.exceptions import ObjectDoesNotExist

from .utils import encrypt_message
from chat.temperature import apply_temperature_changes


def chat_open_message(chat_room):
    from .models import ChatMessage
    location = chat_room.name.split("_")[1]
    open_message = f"{location} 채팅방이 열렸습니다."
    
    ChatMessage.objects.create(
        chat_room = chat_room, 
        message = encrypt_message(open_message), 
        user = None,
        is_system = True
    )
    return open_message

@shared_task
def chat_send_time_message(chat_room_id, message=""):
    from .models import ChatMessage, ChatRoom
    
    chat_room = ChatRoom.objects.get(id=chat_room_id)
    
    chat_message = ChatMessage.objects.create(
        chat_room = chat_room, 
        message = encrypt_message(message), 
        user = None,
        is_system = True
    )
    
    channel_layer = get_channel_layer()
    print(f"채팅 이름: {chat_room.name}")
    try:
        async_to_sync(channel_layer.group_send)(
            chat_room.name,
            {
                "type": "system_send",
                "message": message,
                "timestamp" : chat_message.created_at.isoformat()
            }
        )
        print("전송 되었습니다.")
    except Exception as e:
        print(f"메시지 전송 실패: {e}") 

@shared_task
def delete_chat_room(chat_room_id):
    from chat.models import ChatRoom
    try:
        chat_room = ChatRoom.objects.get(id=chat_room_id)
        #매너 온도 변경사항 적용
        apply_temperature_changes(chat_room)
        #매너 온도 변경시 채팅방 삭제
        chat_room.delete()
        print(f"ChatRoom {chat_room.name} deleted.")
    except ChatRoom.DoesNotExist:
        print(f"ChatRoom {chat_room.name} does not exist.")
        pass
    