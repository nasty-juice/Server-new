from channels.generic.websocket import AsyncWebsocketConsumer
import json
from .models import MatchingQueue, MatchRequest
from django.http import JsonResponse
from my_app.models import CustomUser
from asgiref.sync import sync_to_async, async_to_sync

NEED_USERNUM = 1

class StartMatching(AsyncWebsocketConsumer):
    async def connect(self):
        self.location = self.scope["url_route"]["kwargs"]["location"]
        self.user = self.scope["user"]
        
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        location = text_data_json['location']
        userNumber = text_data_json['student_number']
        userName = text_data_json['user_name']
        action = text_data_json['action']
        print(location + " " + userNumber + " " + userName)
        
        #매칭 수락 거절 받기
        if action == 'accept_match':
            await self.accept_match(userNumber, location)
            return
        elif action == 'reject_match':
            await self.reject_match(userNumber, location)
            return
        
        #유저 학번으로 찾기
        user = await self.get_user_by_number(userNumber)
        
        #장소 데이터 불러오기
        targetQueue = await self.get_or_create_queue(location)
        
        print(user.username + " " + targetQueue.name)
        
        #큐에 존재하는지 확인, 사용자 추가
        already_in_queue = await self.check_user_in_queue(user,targetQueue)
        if already_in_queue:
            await self.send(text_data=json.dumps({'status': 'you already in another queue'}))
            return
        
        user_join_room = await sync_to_async(lambda: user.join_room)()
        if user_join_room is None:
            await self.add_user_to_queue(user, targetQueue)
            canMatch = True
        else:
            await self.send(text_data=json.dumps({'status': 'you already have room'}))
            canMatch = False
    
        queue_size = await sync_to_async(lambda: targetQueue.users.count())()
        
        #매칭 로직 
        if canMatch:
            if queue_size >= NEED_USERNUM:
                users_to_match = await sync_to_async(lambda: list(targetQueue.users.all()[:NEED_USERNUM]))()
                await self.confirm_match(users_to_match, location, targetQueue)
                self.send(text_data=json.dumps({'status': 'matched'}))
            else:
                await self.send(text_data=json.dumps({'status': 'waiting'}))
    
    @sync_to_async
    def remove_users_from_queue(self, queue_instance, users):
        queue_instance.users.remove(*users)
        
    async def confirm_match(self, users, location, targetQueue):
        confirm_match = await sync_to_async(MatchRequest.objects.create)(location_name=location)
        self.room_group_name = f"matching_{confirm_match.id}"

        #그룹으로 새롭게 묶음
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await sync_to_async(confirm_match.confirm_users.set)(users)
        await sync_to_async(confirm_match.save)()
        
        # targetQueue에서 사용자 제거
        await sync_to_async(targetQueue.users.remove)(*users)
        
        # 그룹에 사용자 추가
        group_name = f"matching_{confirm_match.id}"
        
        #사용자들 그룹으로 묶기
        for user in users:
            await self.channel_layer.group_add(
                group_name,
                self.channel_name
            )
        
        #그룹에 매칭 여부 전송
        await self.channel_layer.group_send(
            group_name,
            {
                "type": "match_request",
                "message": "매칭을 수락하시겠습니까?",
                "status": "matched",
                "match_request_id": confirm_match.id
            }
        )
    
    async def match_request(self, event):
        message = event['message']
        status = event['status']
        print(f"메시지: {message}")
        
        try:
            await self.send(text_data=json.dumps({
                "message" : message,
                "status": status, 
            }))
        except Exception as e:
            print(f"메시지 전송 실패: {e}")
    
    @sync_to_async
    def get_user_by_number(self, number):
        try:
            return CustomUser.objects.filter(student_number=number).first()
        except CustomUser.DoesNotExist:
            return None
    
    @sync_to_async
    def get_or_create_queue(self, location):
        targetQueue = MatchingQueue.objects.filter(name=location)
        if targetQueue.exists():
            return targetQueue.first()
        else:
            return MatchingQueue.objects.create(name=location)
    
    #모든 대기열에서 사용자 확인
    @sync_to_async
    def check_user_in_queue(self, user, targetQueue):
        other_queues = MatchingQueue.objects.exclude(id=targetQueue.id)
        
        for queue in other_queues:
            if queue.users.filter(id=user.id).exists():
                return True
        return False

    #대기열에 사용자 추가
    @sync_to_async
    def add_user_to_queue(self, user, queue_instance):
        queue_instance.users.add(user)
        queue_instance.save()
    
    #사용자가 매칭 수락
    async def accept_match(self, student_number, location):
        user = await self.get_user_by_number(student_number)
        match_request = await self.get_match_request(location)
        await sync_to_async(match_request.confirm_users.add)(user)
        
        confirm_user_count = await sync_to_async(match_request.confirm_users.count)()
        total_user_count = await sync_to_async(match_request.users.count)()
        
        if confirm_user_count == total_user_count:
            await self.channel_layer.group_send(
                f"matching_{match_request.id}",
                {
                    "type": "match_confirmed",
                    "message": "모든 사용자가 매칭을 수락했습니다.",
                    "status": "confirmed"
                }
            )

    #사용자가 매칭 거절
    async def reject_match(self, student_number, location):
        user = await self.get_user_by_number(student_number)
        match_request = await self.get_match_request(location)
        await sync_to_async(match_request.confirm_users.remove)(user)
        
        await self.channel_layer.group_send(
            f"matching_{match_request.id}",
            {
                "type": "match_rejected",
                "message": f"{user.username}님이 매칭을 거절했습니다.",
                "status": "rejected"
            }
        )