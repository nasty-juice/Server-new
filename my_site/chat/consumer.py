import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from .models import ChatMessage, ChatRoom
from asgiref.sync import sync_to_async
from django.core.exceptions import ObjectDoesNotExist
from .temperature import add_temperature_change, apply_temperature_changes
from .utils import check_all_user_in_chatroom, get_db_chatroom_messages, encrypt_message, decrypt_message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"
        self.user = self.scope["user"]
        print(f'room_name : {self.room_name}')
        print(f'user : {self.user}')

        #ChatRoom 확인
        chatRoom = await sync_to_async(lambda: ChatRoom.objects.get(name=self.room_name))()
        # #사용자 방 확인
        user_join_room = await sync_to_async(lambda: self.user.join_room)()
        
        if user_join_room is None or user_join_room != chatRoom:
            print("방 권한이 없습니다.")
            await self.close()
            return
        
        #Join room group
        await self.channel_layer.group_add(
            self.room_group_name, 
            self.channel_name
        )
        print(f"room_group_name : {self.room_group_name}")
        print(f"channel_layer : {self.channel_layer}")
        
        #웹 소켓 접속 승인
        await self.accept()
        #방에 있는 유저 가져오기
        users = await sync_to_async(check_all_user_in_chatroom)(chatRoom)
        #방에 있는 기존 메시지 불러오기
        try:
            decrypted_messages = await sync_to_async(get_db_chatroom_messages)(chatRoom)
        except Exception as e:
            print(f"메시지 불러오기 실패: {e}")
            return
        #클라이언트에 메시지 전송
        await self.send(text_data=json.dumps({'messages': users, 'action': 'userInfo'}))
        await self.send(text_data=json.dumps({'messages': decrypted_messages}))
    
    async def disconnect(self, close_code):
        #그룹에서 제거
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": "채팅방이 비활성화 되었습니다."
            }
        )
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        
        if message == 'temperature':
            usernum = text_data_json["targetUserNum"]
            action = text_data_json["action"]
            chatRoom = await sync_to_async(lambda: ChatRoom.objects.get(name=self.room_name))()
            await add_temperature_change(chatRoom, self.user.student_number, usernum, action)
            return
        #지워야 함 -> 클라이언트 부분도 같이
        elif message == 'test':
            
            chatRoom = await sync_to_async(lambda: ChatRoom.objects.get(name=self.room_name))()
            await sync_to_async(apply_temperature_changes)(chatRoom)
        
        encrypted_message = await sync_to_async(encrypt_message)(message)
        #메시지를 서버에 저장
        chat_message = await self.save_message(encrypted_message)
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name, {
                "type": 'chat_message', 
                "message": encrypted_message,
                "user_name": self.user.username,
                'timestamp' : chat_message
            }
        )

    #group send 타겟 메서드
    async def chat_message(self, event):
        encrypted_message = event["message"]
        decrypted_message = await sync_to_async(decrypt_message)(encrypted_message)
        #클라이언트에 메시지 전송
        try:
            await self.send(text_data=json.dumps({
                "message": decrypted_message, 
                'user_name' : event['user_name'],
                'timestamp' : event['timestamp']
            }))
        except Exception as e:
            print(f"메시지 전송 실패: {e}")
    
    #시스템 메시지
    async def send_to_group(self, event):
        status = event['status']
        message = event['message']
        encrypted_message = await sync_to_async(encrypt_message)(message)
        await self.save_message(encrypted_message, True)
        # WebSocket에 메시지 전송
        await self.send(text_data=json.dumps({
            "action": status,
            "message": message
        }))
        
    #db에 메시지 저장
    @sync_to_async
    def save_message(self, message, is_system=False):
        try:
            chat_room = ChatRoom.objects.get(name=self.room_name)
            chat_message = ChatMessage.objects.create(chat_room=chat_room ,message=message, is_system=is_system)
            if not is_system:
               chat_message.user = self.user
            
            return chat_message.created_at.isoformat()
        except ObjectDoesNotExist:
            print(f"chatRoom '{self.room_name}' does not exist.")        

    