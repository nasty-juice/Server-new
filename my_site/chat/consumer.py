import json
import logging
import os
import base64

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.fernet import Fernet
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatMessage, ChatRoom
from asgiref.sync import sync_to_async
from django.core.exceptions import ObjectDoesNotExist
from dotenv import load_dotenv
from my_site.settings import BASE_DIR
# .env 파일을 로드
load_dotenv()

logger = logging.getLogger(__name__)

#개인 키 불러오기
private_key_path = os.path.join(BASE_DIR, "keys", "private_key.pem")
with open(private_key_path, "rb") as f:
    private_key = serialization.load_pem_private_key(f.read(),password=None)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"
        self.user = self.scope["user"]
        print(f'room_name : {self.room_name}')
        print(f'user : {self.user}')
        
        # 사용자가 인증되지 않은 경우 기본 사용자 정보 생성
        # if self.scope["user"].is_anonymous:
        #     self.user = await self.get_or_create_user("default_user", "default_user@example.com")
        # else:
        #     self.user = self.scope["user"]

        #ChatRoom 확인
        chatRoom = await sync_to_async(lambda: ChatRoom.objects.get(name=self.room_name))()
        # #사용자 방 확인
        user_join_room = await sync_to_async(lambda: self.user.join_room)()
        
        if user_join_room is None or user_join_room != chatRoom:
            logger.warning("방 권한이 없습니다.")
            await self.close()
            return
        
        #Join room group
        await self.channel_layer.group_add(
            self.room_group_name, 
            self.channel_name
        )
        
        #웹 소켓 접속 승인
        await self.accept()

        #방에 있는 기존 메시지 불러오기
        messages = await self.get_messages()
        decrypted_messages = []
        for message in messages:
            try:
                encrypted_message = message.message
                decrypted_message = private_key.decrypt(
                    encrypted_message,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                ).decode()
                
                decrypted_messages.append({
                    'user_name' : message.user.username,
                    'message' : decrypted_message,
                    'timestamp' : message.created_at.isoformat()
                })
                print(f"복호화된 메시지: {decrypted_message}")
            except Exception as e:
                logger.warning(f"메시지 복호화 실패: {e}")
                
        await self.send(text_data=json.dumps({'messages': decrypted_messages}))
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        
        #공개키 불러오기
        public_key_path = os.path.join(BASE_DIR, "keys", "public_key.pem")
        with open(public_key_path, "rb") as f:
            public_key = serialization.load_pem_public_key(f.read())
        #메시지 암호화
        encrypted_message = public_key.encrypt(
            str(message).encode(),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
    
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

    # Receive message from room group
    async def chat_message(self, event):
        encrypted_message = event["message"]
        #복호화
        try:    
            decrypted_message = private_key.decrypt(
                encrypted_message,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            ).decode()
        except Exception as e:
            logger.warning(f"메시지 복호화 실패: {e}")
            return

        #클라이언트에 메시지 전송
        try:
            await self.send(text_data=json.dumps({
                "message": decrypted_message, 
                'user_name' : event['user_name'],
                'timestamp' : event['timestamp']
            }))
        except Exception as e:
            logger.warning(f"메시지 전송 실패: {e}")
    
    @sync_to_async
    def save_message(self, message):
        try:
            chat_room = ChatRoom.objects.get(name=self.room_name)
            chat_message = ChatMessage.objects.create(chat_room=chat_room, user=self.user ,message=message)
            return chat_message.created_at.isoformat()
        except ObjectDoesNotExist:
            print(f"chatRoom '{self.room_name}' does not exist.")
    
    @sync_to_async
    def get_messages(self):
        try:
            chat_room = ChatRoom.objects.get(name=self.room_name)
            messages = ChatMessage.objects.filter(chat_room=chat_room).order_by('created_at')
            print(f'chatRoom Num : {chat_room.name}')
            
            for msg in messages:
                print(f'{msg.user.username} : {msg.message}')
            
            return messages
        except ObjectDoesNotExist:
            return []

    