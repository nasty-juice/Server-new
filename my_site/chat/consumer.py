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
from my_app.models import CustomUser
from asgiref.sync import sync_to_async
from django.core.exceptions import ObjectDoesNotExist
from dotenv import load_dotenv
from my_site.settings import BASE_DIR
# .env 파일을 로드
load_dotenv()

logger = logging.getLogger(__name__)

#개인 키 불러오기
private_key_path = os.path.join(BASE_DIR, "private_key.pem")
with open(private_key_path, "rb") as f:
    private_key = serialization.load_pem_private_key(f.read(),password=None)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"
        self.user = self.scope["user"]
        
        tryUser = await database_sync_to_async(self.get_user_by_username)(self.user.username)
        #사용자 인증 확인
        if not self.user.is_authenticated:
            logger.warning("로그인 페이지로 이동")
            return

        #사용자 방 권한 확인
        try:
            if str(tryUser.join_room) != str(self.room_name):
                logger.warning("방 권한이 없습니다.")
                return
        except CustomUser.DoesNotExist:
            logger.warning("사용자가 존재하지 않습니다.")
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name, 
            self.channel_name
        )
        # 웹 소켓 접속 승인
        await self.accept()

        #방에 있는 기존 메시지 불러오기
        messages = await self.get_messages()
        decrypted_messages = []
        for message in messages:
            try:
                #encoded_message = message['message']
                #encrypted_message = base64.b64decode(encoded_message)
                encrypted_message = message['message']
                #decrypted_message = encrypted_message
                decrypted_message = private_key.decrypt(
                    encrypted_message,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                ).decode()
                
                decrypted_messages.append({
                    'user_id' : message["user_id"],
                    'user_name' : message["user_name"],
                    'message' : decrypted_message
                })
                print(f"복호화된 메시지: {decrypted_message}")
            except Exception as e:
                logger.warning(f"메시지 복호화 실패: {e}")
                
        await self.send(text_data=json.dumps({'messages': decrypted_messages}))
    
    def get_user_by_username(self, username):
        return CustomUser.objects.filter(username=username).first()
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        user_id = text_data_json['user_id']
        user_name = text_data_json['user_name']

        #공개키 불러오기
        with open("public_key.pem", "rb") as f:
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
        await self.save_message(user_id, encrypted_message)
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name, {
                "type": 'chat.message', 
                "message": encrypted_message, 
                'user_id' : user_id, 
                'user_name' : user_name
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        encrypted_message = event["message"]
        user_id = event["user_id"]
        user_name = event['user_name']
        
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