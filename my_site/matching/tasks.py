from celery import shared_task
from chat.temperature import apply_temperature_changes

@shared_task
def delete_chat_room(chatroom_name):
    from chat.models import ChatRoom
    try:
        chat_room = ChatRoom.objects.filter(name=chatroom_name).first()
        #매너 온도 변경사항 적용
        apply_temperature_changes(chat_room)
        chat_room.delete()
        print(f"ChatRoom {chatroom_name} deleted.")
    except ChatRoom.DoesNotExist:
        print(f"ChatRoom {chatroom_name} does not exist.")
        pass
    
@shared_task
def test():
    print("테스트 작업 실행됨")