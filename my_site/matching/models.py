from django.db import models
from my_app.models import CustomUser
from matching2.models import FriendGroup
# Create your models here.

class MatchingQueue(models.Model):
    name = models.CharField(max_length=100)
    groups = models.ManyToManyField(FriendGroup, related_name='queue',blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    location = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

# 유저가 거절 누르면 바로 대기가 풀어지는지, 시간 기다리는지 확인하기

#매칭 임시 그룹 - 수락 누르면 대화방 권한 주는걸로
class MatchRequest(models.Model):
    name = models.CharField(max_length=100, unique=True, default='match_request')
    location_name = models.CharField(max_length=100)
    confirm_users = models.ManyToManyField(CustomUser, related_name='confirm_group',blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
