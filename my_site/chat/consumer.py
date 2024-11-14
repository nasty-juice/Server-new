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
from datetime import datetime
# .env 파일을 로드
load_dotenv()

logger = logging.getLogger(__name__)

#개인 키 불러오기
private_key_path = os.path.join(BASE_DIR, "private_key.pem")
with open(private_key_path, "rb") as f:
    private_key = serialization.load_pem_private_key(f.read(),password=None)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"chat_{self.room_id}"
        self.user = self.scope["user"]
        #self.user = await self.get_or_create_user("정세현", "default_user@example.com")
        
        # if not self.user.is_authenticated:
        #     logger.warning("로그인 페이지로 이동")
        #     await self.close()
        #     return
        
        try:
            tryUser = await database_sync_to_async(self.get_user_by_number)(self.user.student_number)
        except CustomUser.DoesNotExist:
            logger.warning("사용자가 존재하지 않습니다.")
            await self.close()
            return

        #ChatRoom 확인 및 생성
        chatRoom = await self.get_or_create_chat_room(self.room_id)
        #사용자 방 권한 확인
        tryUser_join_room = await sync_to_async(lambda: tryUser.join_room)()
        checkUser_join_room = await sync_to_async(lambda: self.user.join_room)()
        
        try:
            if tryUser_join_room != checkUser_join_room:
                logger.warning("방 권한이 없습니다.")
                await self.close()
                return
        except AttributeError:
            logger.warning("사용자가 방에 속해있지 않습니다.")
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
        # messages = await self.get_messages()
        # decrypted_messages = []
        # for message in messages:
        #     try:
        #         encrypted_message = message.message
        #         decrypted_message = private_key.decrypt(
        #             encrypted_message,
        #             padding.OAEP(
        #                 mgf=padding.MGF1(algorithm=hashes.SHA256()),
        #                 algorithm=hashes.SHA256(),
        #                 label=None
        #             )
        #         ).decode()
                
        #         decrypted_messages.append({
        #             'student_number' : message.user.student_number,
        #             'user_name' : message.user.username,
        #             'message' : decrypted_message,
        #             'timestamp' : message.created_at.isoformat()
        #         })
        #         print(f"복호화된 메시지: {decrypted_message}")
        #     except Exception as e:
        #         logger.warning(f"메시지 복호화 실패: {e}")
                
        # await self.send(text_data=json.dumps({'messages': decrypted_messages}))
    
    def get_user_by_number(self, number):
        return CustomUser.objects.filter(student_number=number).first()
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        user_num = text_data_json['user_num']
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
        chat_message = await self.save_message(user_num, encrypted_message)
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name, {
                "type": 'chat_message', 
                "message": encrypted_message, 
                'user_num' : user_num, 
                'user_name' : user_name,
                'timestamp' : chat_message
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        encrypted_message = event["message"]
        user_num = event["user_num"]
        user_name = event['user_name']
        timestamp = event['timestamp']
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
                'user_num': user_num,
                'user_name' : user_name,
                'timestamp' : timestamp
            }))
        except Exception as e:
            logger.warning(f"메시지 전송 실패: {e}")
    
    @sync_to_async
    def save_message(self, user_num, message):
        try:
            chat_room = ChatRoom.objects.get(id=self.room_id)
            user = CustomUser.objects.get(student_number=user_num)
            chat_message = ChatMessage.objects.create(chat_room=chat_room, user=user ,message=message)
            return chat_message.created_at.isoformat()
        except ObjectDoesNotExist:
            print(f"chatRoom '{self.room_id}' does not exist.")
    
    @sync_to_async
    def get_messages(self):
        try:
            chat_room = ChatRoom.objects.get(id = self.room_id)
            messages = ChatMessage.objects.filter(chat_room=chat_room).order_by('created_at')
            print(f'chatRoom Num : {chat_room.name}')
            
            for msg in messages:
                print(f'{msg.user.username} : {msg.message}')
            
            return messages
        except ObjectDoesNotExist:
            return []
    
    @sync_to_async
    def get_or_create_chat_room(self, room_id):
        try:
            return ChatRoom.objects.get(id=room_id)
        except ObjectDoesNotExist:
            return ChatRoom.objects.create(id=room_id, name=f"room_{room_id}")
        
    @sync_to_async
    def get_or_create_user(self, username, email):
        user, created = CustomUser.objects.get_or_create(username=username, defaults={'email': email})
        user.student_number = "60202247"
        return user