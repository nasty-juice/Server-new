import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer
from .models import ChatMessage, ChatRoom
from my_app.models import CustomUser
from asgiref.sync import sync_to_async

from django.core.exceptions import ObjectDoesNotExist

logger = logging.getLogger(__name__)
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"
        self.user = self.scope["user"]
        #사용자 인증 확인
        if not self.user.is_authenticated:
            logger.warning("로그인 페이지로 이동")
            return
        #사용자 방 권한 확인
        try:
            tryUser = await CustomUser.objects.get(user=self.user)
            if tryUser.chatRoom != self.room_name:
                logger.warning("방 권한이 없습니다.")
                return
        except CustomUser.DoesNotExist:
            logger.warning("사용자가 존재하지 않습니다.")
            return
        
        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        #방에 있는 기존 메시지 불러오기
        messages = await self.get_messages()
        print(messages)
        await self.send(text_data=json.dumps({'messages': messages}))
        
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        user_id = text_data_json['user_id']
        user_name = text_data_json['user_name']

        #메시지를 서버에 저장
        await self.save_message(user_id, message)
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name, {"type": 'chat.message', "message": message, 'user_id' : user_id, 'user_name' : user_name}
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event["message"]
        user_id = event["user_id"]
        user_name = event['user_name']
        # Send message to WebSocket
        try:
            await self.send(text_data=json.dumps({
                "message": message, 
                'user_id': user_id,
                'user_name' : user_name,
            }))
        except Exception as e:
            logger.warning(f"메시지 전송 실패: {e}")
    
    @sync_to_async
    def save_message(self, user_id, message):
        try:
            chat_room = ChatRoom.objects.get(name=self.room_name)
            ChatMessage.objects.create(chat_room=chat_room, user_id=user_id, message=message)
        except ObjectDoesNotExist:
            print(f"chatRoom '{self.room_name}' does not exist.")
    
    @sync_to_async
    def get_messages(self):
        try:
            chat_room = ChatRoom.objects.get(name = self.room_name)
            messages = ChatMessage.objects.filter(chat_room=chat_room).order_by('created_at')
            print(f'chatRoom Num : {chat_room.name}')
            
            for msg in messages:
                print(f'{msg.user.username} : {msg.message}')
            
            return [{'user_id' : msg.user.id, 'user_name': msg.user.username, 'message': msg.message} for msg in messages]
        except ObjectDoesNotExist:
            return []