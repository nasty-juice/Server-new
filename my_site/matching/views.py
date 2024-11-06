from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import MatchingQueue, UserGroup
from my_app.models import CustomUser
from .user_queue import userQueue
from django.contrib.auth.decorators import login_required
import logging
from .matchUser import matchUser, cancelMatch
logger = logging.getLogger(__name__)

def start_matching(request):
    if request.method == 'POST':
        #현재 로그인된 사용자
        user = request.user
        #장소 데이터
        location = request.POST.get('location')
        targetQueue = MatchingQueue.objects.filter(name=location)
        
        #큐 종류 있는지 확인
        if targetQueue.exists():
            queue_instance = targetQueue.first()
        else : 
            queue_instance = MatchingQueue.objects.create(name=location)
        
        #큐에 존재하는지 확인, 사용자 추가
        for queue in MatchingQueue.objects.all():
            if queue.users.filter(id=user.id).exists():
                return JsonResponse({'status':'already_in_queue'})
        else:
            if user.join_room == 0 or user.join_room == None:
                queue_instance.users.add(user)
            else:
                return JsonResponse({'status':'already_have_room'})
        
        queue_size = queue_instance.users.count()
        
        #매칭 로직
        need_userNum = 1
        if queue_size >= need_userNum:
            users_to_match = queue_instance.users.all()[:need_userNum]
            return matchUser(users_to_match)
        else:
            return JsonResponse({'status': 'waiting'})

def start_matching_page(request):
    return render(request, 'matching/start_matching.html')


def cancel_matching(request):
    if request.method == 'POST':
        user = request.user
        
        cancelMatch(user)
    
    return JsonResponse({'status': 'none'})

def group_page(request, group_id):
    group = UserGroup.objects.get(id=group_id)
    if request.user in group.users.all():
        return render(request, 'matching/group_page.html',{'group': group})
    else :
        return redirect('some_error_page')
    
def quit_group(request, group_id):
    group = get_object_or_404(UserGroup, id=group_id)
    user = request.user
    
    userExist = group.users.filter(id=user.id).exists()
    if userExist:
        group.users.remove(userExist)
        
        # 그룹에 유저가 없으면 그룹을 삭제
        if group.users.count() == 0:
            group.delete()
            
    return redirect('start_matching_page')


# if queue_size >= 1:
#             users_to_match = queue_instance.users.all()[:2]
#             group = UserGroup.objects.create()
#             logger.debug(users_to_match)
#             for user in users_to_match:
#                 group.users.add(user)
#                 queue_instance.users.remove(user) #큐에서 제거 

#             group.save()
            
#             return redirect('group_page',group_id=group.id)