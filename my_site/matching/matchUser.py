from django.http import HttpResponseRedirect
from chat.models import ChatRoom
from .models import MatchingQueue

def matchUser(users, location):
    chat_room = ChatRoom.objects.create()
    chat_room.name = f"{location}{chat_room.id}"
    chat_room.save()
    
    try:
        for user in users:
            user.join_room = chat_room
            cancelMatch(user)
            user.save()
    except Exception as e:
        chat_room.delete()
        raise e
    
    redirect_url = f'/chat/roomNum/{chat_room.id}/'
    
    return HttpResponseRedirect(redirect_url)
    
def cancelMatch(user):
    for match in MatchingQueue.objects.all():
        if match.users.filter(id=user.id).exists():
            match.users.remove(user)
        