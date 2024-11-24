from channels.generic.websocket import AsyncWebsocketConsumer
import json
import uuid
from .models import MatchingQueue, MatchRequest
from django.http import JsonResponse
from my_app.models import CustomUser
from chat.models import ChatRoom
from asgiref.sync import sync_to_async, async_to_sync
from .utils import get_or_create_queue, check_user_in_queue, update_users_join_room, get_match_request, update_queue_size
from matching.tasks import delete_chat_room 
import asyncio

NEED_USERNUM = 1

class StartMatching(AsyncWebsocketConsumer):
    async def connect(self):
        self.location = self.scope["url_route"]["kwargs"]["location"]
        self.user = self.scope["user"]
        self.confirmed = False
        if self.user.is_anonymous:
            #
            return
        
        self.room_group_name = f"matching_{self.location}"
        self.userNumber = self.user.student_number
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        #웹 소켓 연결 수락
        await self.accept()
        
        #웹 소켓 연결시 바로 실행
        await self.start_match()

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        action = text_data_json['action']
        
        #매칭 수락 거절 받기
        match action:
            case 'accept_match':
                print(f"매칭 수락 요청: {self.user}")
                await self.accept_match()
                return
            case 'reject_match':
                await self.reject_match()
                return
            case 'match_group':
                await self.match_group(text_data_json['new_group_name'])
                return
            case 'cancel_matching':
                print(f"매칭 취소 요청: {self.user}")
                await self.cancel_matching()
                return
            case 'confirmed':
                await self.channel_layer.group_discard(
                    self.room_group_name,
                    self.channel_name
                )
                self.confirmed = True
                return
            
    
    async def start_match(self):
        #장소 데이터 불러오기 //학관, 명진당
        targetQueue = await get_or_create_queue(self.location)
        
        #큐에 존재하는지 확인, 사용자 추가
        already_in_queue = await check_user_in_queue(self.user,targetQueue)
        if already_in_queue:
            await self.send(text_data=json.dumps({'status': 'you already in another queue'}))
            return
        
        #사용자가 이미 방에 있는지 확인
        join_room = await sync_to_async(lambda: self.user.join_room)()
        if join_room is None:
            await sync_to_async(targetQueue.users.add)(self.user)
            await sync_to_async(targetQueue.save)()
             
            # 사용자가 큐에 추가되었을 때 update_queue_size 함수를 호출하여 큐의 크기를 업데이트
            await update_queue_size(self.channel_layer, self.room_group_name, targetQueue)
        else:
            await self.send(text_data=json.dumps({'status': 'you already have room'}))
            return

        queue_size = await sync_to_async(lambda: targetQueue.users.count())()
        
        #매칭 로직
        if queue_size >= NEED_USERNUM:
            #새로운 채널스 그룹 만들기
            await self.create_new_group()
        else:
            await self.send(text_data=json.dumps({'status': 'waiting',}))
    
    async def match_group(self, new_group_name):
        #이미 매칭이 된 상태임
        await self.channel_new_group(new_group_name)
        
        try:
            confirm_match = await sync_to_async(MatchRequest.objects.create)(name=self.new_group_name,location_name=self.location)
            await sync_to_async(confirm_match.confirm_users.clear)()
            await sync_to_async(confirm_match.save)()
            print(f'{self.user}님의 매칭 요청: {self.new_group_name}')
            #강제로 시간 대기 -> 각 클라이언트가 새로운 그룹 연결이 성공적으로 이루어진 후 작동해야함
            await asyncio.sleep(0.1)
            await self.send_confirm_match()
        except Exception as e:
            return
        
    async def accept_match(self):
        match_request = await get_match_request(self.new_group_name)
        if match_request is None:
            await self.send(text_data=json.dumps({'status': 'error','message': '매칭 요청이 존재하지 않습니다.'}))
            return
        
        user_exist = await sync_to_async(lambda: match_request.confirm_users.filter(id=self.user.id).exists())()
        print(f"match_request: {match_request.name}")
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
            try:
                delete_chat_room.apply_async((chat_room.name,), countdown=3600)
            except Exception as e:
                print(f"delete_chat_room task 실행 중 오류 발생: {e}")
            
            await sync_to_async(match_request.delete)()
            
            # 모든 사용자의 join_room 필드를 업데이트
            await update_users_join_room(all_users, chat_room)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "send_to_group",
                    "message": chat_room_name,
                    "status": "confirmed"
                }
            )
    
    async def reject_match(self):
        match_request = await get_match_request(self.new_group_name)
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
        print(f"{self.user} : 새로운 채널 입장 완료")
    
    #매칭 수락 여부 각 클라에 보내기
    async def send_confirm_match(self):        
        # targetQueue에서 사용자 제거
        targetQueue = await get_or_create_queue(self.location)
        users = await sync_to_async(lambda: list(targetQueue.users.all()[:NEED_USERNUM]))()
        
        await sync_to_async(targetQueue.users.remove)(*users)
        await sync_to_async(targetQueue.save)()
        
        #유저 데이터 묶어서 보내기
        user_data = []
        for user in users:
            try:
                user_info = {
                    'user_number': user.student_number,
                    'user_temperature': float(user.temperature),
                }
                user_data.append(user_info)
            except Exception as e:
                print(f"유저 데이터 처리 중 오류 발생: {e}")
                continue
        
        print(f"매칭된 유저: {user_data}")
        print(f"유저 데이터: {json.dumps(user_data)}")
        
        #그룹에 매칭 여부 전송
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "send_to_group",
                "message": user_data,
                "status": "matched",    
            }
        )
        
        # 타이머 설정
        async def send_timer():
            for currTime in range(15, 0, -1):
                if self.confirmed:
                    return
                
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "send_to_group",
                        "message": currTime,
                        "status": "matchTimer",    
                    },
                )
                await asyncio.sleep(1)
        
            match_request = await get_match_request(self.new_group_name)
            if match_request is not None:
                await sync_to_async(match_request.delete)()
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "send_to_group",
                        "message": "timeOut",
                        "status": "matchTimer",    
                    },
                )
        
        asyncio.create_task(send_timer())

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
        
    async def cancel_matching(self):
        targetQueue = await (get_or_create_queue(self.location))
        await sync_to_async(targetQueue.users.remove)(self.user)
        await sync_to_async(targetQueue.save)()
        
        # 사용자가 큐에서 제거되었을 때 update_queue_size 함수를 호출하여 큐의 크기를 업데이트
        await update_queue_size(self.channel_layer, self.room_group_name, targetQueue)
        
        await self.send(text_data=json.dumps({'status': 'cancel_matching'}))   