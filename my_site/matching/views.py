from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import MatchingQueue, UserGroup
from my_app.models import CustomUser
from .user_queue import userQueue
from django.contrib.auth.decorators import login_required
import logging

logger = logging.getLogger(__name__)
#
# def start_matching(request):
#     if request.method == 'POST':
#         user = request.user
#         userQueue.start_matching(user)
    
#         return JsonResponse({'status':'Matching...'})
#     else:
#         print("Wrong Request")


#모델을 이용한 랜덤 큐 방식
def start_matching(request):
    if request.method == 'POST':
        #현재 로그인된 사용자
        user = request.user
        
        #큐에 존재하는지 확인
        if MatchingQueue.objects.filter(user=user).exists():
            return JsonResponse({'status':'already_in_queue'})
        else :
            #큐에 사용자 추가
            MatchingQueue.objects.create(user=user)
        
        queue_size = MatchingQueue.objects.count()
        
        if queue_size>= 2:
            #매칭 로직
            users_to_match = MatchingQueue.objects.order_by('created_at')[:2]
            group = UserGroup.objects.create()
            logger.debug(users_to_match)
            for user in users_to_match:
                group.users.add(user.user)
                user.delete() #큐에서 제거 

            group.save()
            
            return redirect('group_page',group_id=group.id)
        
    return JsonResponse({'status': 'waiting'})

def start_matching_page(request):
    return render(request, 'matching/start_matching.html')


def cancel_matching(request):
    if request.method == 'POST':
        user = request.user
        
        matching_entry = MatchingQueue.objects.filter(user=user).first()
        if matching_entry:
            matching_entry.delete()
    
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
