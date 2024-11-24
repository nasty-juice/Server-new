from celery import shared_task

@shared_task
def delete_chat_room(chatroom_name):
    from chat.models import ChatRoom
    try:
        chat_room = ChatRoom.objects.filter(name=chatroom_name).first()
        chat_room.delete()
        print(f"ChatRoom {chatroom_name} deleted.")
    except ChatRoom.DoesNotExist:
        print(f"ChatRoom {chatroom_name} does not exist.")
        pass
    
@shared_task
def test():
    print("테스트 작업 실행됨")