from asgiref.sync import sync_to_async
from .models import MatchingQueue, MatchRequest

@sync_to_async
def get_or_create_queue(location):
    targetQueue = MatchingQueue.objects.filter(name=location)
    if targetQueue.exists():
        return targetQueue.first()
    else:
        return MatchingQueue.objects.create(name=location)

#모든 대기열에서 사용자 확인
@sync_to_async
def check_user_in_queue(user, targetQueue):
    other_queues = MatchingQueue.objects.exclude(id=targetQueue.id)
    
    for queue in other_queues:
        if queue.users.filter(id=user.id).exists():
            return True
    return False

@sync_to_async
def update_users_join_room(users, chat_room):
    for user in users:
        user.join_room = chat_room
        user.save()

@sync_to_async
def get_match_request(request_name):
    try:
        return MatchRequest.objects.filter(name=request_name).first()
    except MatchRequest.DoesNotExist:
        return None
    