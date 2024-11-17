from channels.generic.websocket import AsyncWebsocketConsumer
import json
import uuid
from .models import MatchingQueue, MatchRequest
from django.http import JsonResponse
from my_app.models import CustomUser
from chat.models import ChatRoom
from asgiref.sync import sync_to_async, async_to_sync

NEED_USERNUM = 2

class StartMatching(AsyncWebsocketConsumer):
    async def connect(self):
        self.location = self.scope["url_route"]["kwargs"]["location"]
        self.user = self.scope["user"]
        self.room_group_name = f"matching_{self.location}"
        self.userNumber = self.user.student_number
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        #웹 소켓 연결시 바로 실행
        await self.start_match()

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        action = text_data_json['action']
        
        #매칭 수락 거절 받기
        match action:
            case 'accept_match':
                await self.accept_match()
                return
            case 'reject_match':
                await self.reject_match()
                return
            case 'match_group':
                await self.match_group(text_data_json['new_group_name'])
                return
            
    
    async def start_match(self):
        #장소 데이터 불러오기 //학관, 명진당
        targetQueue = await self.get_or_create_queue()
        
        #큐에 존재하는지 확인, 사용자 추가
        already_in_queue = await self.check_user_in_queue(targetQueue)
        if already_in_queue:
            await self.send(text_data=json.dumps({'status': 'you already in another queue'}))
            return
        
        #사용자가 이미 방에 있는지 확인
        join_room = await sync_to_async(lambda: self.user.join_room)()
        if join_room is None:
            await sync_to_async(targetQueue.users.add)(self.user)
            await sync_to_async(targetQueue.save)()
        else:
            await self.send(text_data=json.dumps({'status': 'you already have room'}))
            return

        queue_size = await sync_to_async(lambda: targetQueue.users.count())()
        #매칭 로직
        if queue_size >= NEED_USERNUM:
            #새로운 채널스 그룹 만들기
            await self.create_new_group()
        else:
            await self.send(text_data=json.dumps({'status': 'waiting'}))
    
    async def match_group(self, new_group_name):
        #이미 매칭이 된 상태임
        await self.channel_new_group(new_group_name)
        
        try:
            confirm_match = await sync_to_async(MatchRequest.objects.create)(name=self.new_group_name,location_name=self.location)
        except Exception as e:
            return
        
        await sync_to_async(confirm_match.confirm_users.clear)()
        await sync_to_async(confirm_match.save)()
        
        await self.send_confirm_match()
        
    async def accept_match(self):
        match_request = await self.get_match_request(self.new_group_name)
        if match_request is None:
            await self.send(text_data=json.dumps({'status': 'error','message': '매칭 요청이 존재하지 않습니다.'}))
            return
        
        user_exist = await sync_to_async(lambda: match_request.confirm_users.filter(id=self.user.id).exists())()
        
        if not user_exist:
            await sync_to_async(match_request.confirm_users.add)(self.user)
            await sync_to_async(match_request.save)()
            await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "send_to_group",
                "message": f"{self.user.username}님이 매칭을 수락했습니다.",
                "status": "accepted"
            }
        )
        else:
            await self.send(text_data=json.dumps({'status': 'error','message': '이미 매칭을 수락했습니다.'}))
            return
        
        confirm_user_count = await sync_to_async(match_request.confirm_users.count)()
        if confirm_user_count == NEED_USERNUM:
            all_users = await sync_to_async(lambda: list(match_request.confirm_users.all()))()
            chat_room_name = f"{match_request.location_name}_{uuid.uuid4()}"
            chat_room = await sync_to_async(lambda: ChatRoom.objects.create(name=chat_room_name))()
            
            #ChatRoom에 모든 사용자 추가
            #await self.add_users_to_chat_room(chat_room, all_users)
            
            # 모든 사용자의 join_room 필드를 업데이트
            await self.update_users_join_room(all_users, chat_room)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "send_to_group",
                    "message": "모든 사용자가 매칭을 수락했습니다.",
                    "status": "confirmed"
                }
            )
            
            await sync_to_async(match_request.delete)()
    
    async def reject_match(self):
        match_request = await self.get_match_request(self.new_group_name)
        if match_request is None:
            await self.send(text_data=json.dumps({'status': 'error','message': '매칭 요청이 존재하지 않습니다.'}))
            return
        
        await sync_to_async(match_request.confirm_users.remove)(self.user)
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "send_to_group",
                "message": f"{self.user.username}님이 매칭을 거절했습니다.",
                "status": "rejected"
            }
        )
        
    #기존 그룹 삭제 후 새로운 그룹 형성 - 각 클라이언트 마다 실행되어야 함
    async def channel_new_group(self, new_group_name):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        self.new_group_name = new_group_name
        self.room_group_name = self.new_group_name
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
    
    #매칭 수락 여부 각 클라에 보내기
    async def send_confirm_match(self):        
        # targetQueue에서 사용자 제거
        targetQueue = await self.get_or_create_queue()
        users = await sync_to_async(lambda: list(targetQueue.users.all()[:NEED_USERNUM]))()
    
        await sync_to_async(targetQueue.users.remove)(*users)
        await sync_to_async(targetQueue.save)()
        
        #그룹에 매칭 여부 전송
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "send_to_group",
                "message": "매칭을 수락하시겠습니까?",
                "status": "matched",
            }
        )
    
    async def create_new_group(self):
        #그룹 전체에 메시지를 전송
        self.new_group_name = f"matching_{self.location}_{uuid.uuid4()}"
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "send_to_group",
                "status": "new_group",
                "message": self.new_group_name,
            }
        )
        
    async def send_to_group(self, event):
        status = event['status']
        try:
            response = {
                "status": status, 
            }
            
            if 'message' in event:
                response["message"] = event['message']
            if 'request_name' in event:
                response["request_name"] = event['request_name']
            
            await self.send(text_data=json.dumps(response))
        except Exception as e:
            print(f"메시지 전송 실패: {e}")
    
    @sync_to_async
    def get_or_create_queue(self):
        targetQueue = MatchingQueue.objects.filter(name=self.location)
        if targetQueue.exists():
            return targetQueue.first()
        else:
            return MatchingQueue.objects.create(name=self.location)
    
    #모든 대기열에서 사용자 확인
    @sync_to_async
    def check_user_in_queue(self, targetQueue):
        other_queues = MatchingQueue.objects.exclude(id=targetQueue.id)
        
        for queue in other_queues:
            if queue.users.filter(id=self.user.id).exists():
                return True
        return False
    
    @sync_to_async
    def update_users_join_room(self, users, chat_room):
        for user in users:
            user.join_room = chat_room
            user.save()
    
    @sync_to_async
    def get_match_request(self, request_name):
        try:
            return MatchRequest.objects.filter(name=request_name).first()
        except MatchRequest.DoesNotExist:
            return None
    
    
        