from django.http import HttpResponseRedirect
from chat.models import ChatRoom
from .models import MatchingQueue

room_num = 1
def matchUser(users):
    global room_num
    chat_room = ChatRoom.objects.create(name=room_num)
    
    for user in users:
        user.join_room = room_num
        cancelMatch(user)
        user.save()
    
    room_num+=1
    redirect_url = f'/chat/roomNum/{chat_room.name}/'
    
    return HttpResponseRedirect(redirect_url)
    

def cancelMatch(user):
    for match in MatchingQueue.objects.all():
        if match.users.filter(id=user.id).exists():
            match.users.remove(user)
        