from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import json
from matching.models import MatchingQueue
from asgiref.sync import sync_to_async
from .models import InvitationRequest
from django.utils import timezone
from my_app.models import CustomUser
from redis import asyncio as aioredis
import asyncio
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class Matching(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set up Redis connection
        self.redis = aioredis.from_url("redis://localhost")
        self.unique_channel_name = None

    async def connect(self):
        self.user = self.scope["user"]
        if self.user.is_anonymous:
            return
        
        # CustomUser 모델에 channel_name 저장
        self.user.channel_name = self.channel_name
        await sync_to_async(self.user.save)()

        self.unique_channel_name = f"user_{self.user.student_number}"
        print(self.unique_channel_name)
        await self.channel_layer.group_add(
            self.unique_channel_name,
            self.channel_name
        )
        
        await self.accept()
        
    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            action = text_data_json.get("action")
            if not action:
                await self.send_error("Invalid action", 400)
                return

            match action:
                case "get_meal_status":
                    meal_data = await self.get_meal_waiting_status()
                    await self.send_response("meal_status", meal_data)
                
                case "get_taxi_status":
                    taxi_data = await self.get_taxi_waiting_status()
                    await self.send_response("taxi_status", taxi_data)
                
                case "invite_friend":
                    friend_id = text_data_json.get("friend_id")
                    if not friend_id:
                        await self.send_error("Friend ID is required", 400)
                        return
                    await self.invite_friend(friend_id)
                
                case "accept_invitation":
                    invitation_id = text_data_json.get("invitation_id")
                    await self.accept_invitation(invitation_id)
                
                case "reject_invitation":
                    invitation_id = text_data_json.get("invitation_id")
                    await self.reject_invitation(invitation_id)
                
                case _:
                    await self.send_error("Invalid action", 400)
        except Exception as e:
            await self.send_error(f"Unhandled error: {str(e)}", 500)
    
    async def disconnect(self, close_code):
        if self.unique_channel_name:
            await self.channel_layer.group_discard(self.unique_channel_name, self.channel_name)
            if hasattr(self, "redis"):
                await self.redis.delete(self.unique_channel_name)
                await self.redis.aclose()
            
    async def get_meal_waiting_status(self):
        RESTAURANT_LIST = ['student_center', 'myeongjin', 'staff_cafeteria', 'welfare']
        meal_queues = await database_sync_to_async(list)(
            MatchingQueue.objects.filter(name__in=RESTAURANT_LIST)
        )
        response_data = {name: 0 for name in RESTAURANT_LIST}
        for queue in meal_queues:
            response_data[queue.name] = await database_sync_to_async(queue.users.count)()
        return response_data

    async def get_taxi_waiting_status(self):
        route_list = ['mju_to_station', 'station_to_mju']
        taxi_queues = await database_sync_to_async(list)(
            MatchingQueue.objects.filter(name__in=route_list)
        )
        response_data = {route: 0 for route in route_list}
        for queue in taxi_queues:
            response_data[queue.name] = await database_sync_to_async(queue.users.count)()
        return response_data

    async def invite_friend(self, friend_id): 
        try:
            # 초대 유효성 검사
            self.validate_invitation_request(friend_id)
            
            # 1. 친구 DB 조회
            friend = await self.find_friend_in_db(friend_id)
            
            # 2. 친구 연결 상태 확인
            if not await self.is_friend_connected(friend.student_number):
                await self.send_error("Friend is not connected", 404)
                return
            
             # 초대 상태 확인
            await self.check_existing_invitations(self.user, friend)

            # 초대 생성
            invitation = await self.create_invitation(self.user, friend)
            
            # 초대 알림 전송
            await self.send_invitation_notification(invitation)
            
            # 초대 성공 메시지 전송
            await self.send_response("invitation_sent", {
                "invitation_id": invitation.id,
                "sender_id": invitation.sender.student_number,
                "receiver_id": invitation.receiver.student_number,
            })
            
            self.reject_task = asyncio.create_task(self.auto_reject_invitation(invitation.id))
            return friend

        except CustomUser.DoesNotExist as e:
            await self.send_error("Friend not found", 404)
            print(f"Error: {e}")
            return None

        except Exception as e:
            await self.send_error(f"Failed to invite friend: {str(e)}", 500)
            print(f"Unhandled Error: {e}")
            return None
    
    async def is_friend_connected(self, friend_student_number):
        group_name = f"user_{friend_student_number}"
        print(f"Checking WebSocket connection for group '{group_name}'")
        return await self.check_websocket_connection(group_name)
    
    async def send_invitation_notification(self, invitation):
        """Send an invitation notification to the receiver."""
        await self.channel_layer.group_send(
            f"user_{invitation.receiver.student_number}",
            {
                "type": "send_invitation",
                "invitation_id": invitation.id,
            }
        )

    async def create_invitation(self, user, friend):
        """Create and return a new invitation."""
        invitation = await sync_to_async(InvitationRequest.objects.create)(
            sender=user,
            receiver=friend,
            status="pending",
            created_at=timezone.now()
        )
        await sync_to_async(user.sent_invites.add)(invitation)
        await sync_to_async(user.save)()
        return invitation

    async def check_existing_invitations(self, user, friend):
        """Check for existing invitations for both sender and receiver."""
        sender_to_receiver = await sync_to_async(InvitationRequest.objects.filter)(receiver=friend, sender=user)
        receiver_to_sender = await sync_to_async(InvitationRequest.objects.filter)(receiver=user, sender=friend)
        
        if await sync_to_async(sender_to_receiver.exists)():
            raise Exception("You have already sent an invitation to this friend")
        
        if await sync_to_async(receiver_to_sender.exists)():
            raise Exception("You have already received an invitation from this friend")
        
        if await sync_to_async(user.sent_invites.exists)():
            raise Exception("Sender has an existing invitation")
        
        if await sync_to_async(friend.received_invites.exists)():
            raise Exception("Receiver has an existing invitation")
    
    async def find_friend_in_db(self, friend_id):
        friend = await sync_to_async(CustomUser.objects.get)(student_number=friend_id)
        if not friend:
            raise CustomUser.DoesNotExist(f"User with student_number {friend_id} does not exist")

        return friend
    
    def validate_invitation_request(self, friend_id):
        """Validate the invitation request."""
        if self.user.student_number == friend_id:
            raise Exception("You cannot invite yourself as a friend")
        
    async def check_websocket_connection(self, group_name):
        # Construct the Redis key for the group
        redis_key = f"asgi:group:{group_name}"
        print(redis_key)
        try:
            # Check if the key exists in Redis
            exists = await self.redis.exists(redis_key)

            # Return True if the key exists, False otherwise
            return exists > 0
        except Exception as e:
            # Log the exception (or handle it as needed)
             logger.error(f"Error checking Redis key '{redis_key}': {e}")

        # Return False if there's an error
        return False

    async def auto_reject_invitation(self, invitation_id):
        await asyncio.sleep(15)
        try:
            await self.reject_invitation(invitation_id)
            print(f"Auto-rejected invitation: {invitation_id}")
        except Exception as e:
            print(f"Error auto-rejecting invitation: {e}")

    async def send_invitation(self, event):
        invitation_id = event["invitation_id"]
        await self.send(text_data=json.dumps({
            "type": "invitation",
            "data": {
                "invitation_id": invitation_id,
            }
        }))

    async def send_response(self, response_type, data):
        """Send a structured response to the client."""
        await self.send(text_data=json.dumps({"type": response_type, "data": data}))

    async def send_error(self, message, code):
        """Send an error response to the client."""
        await self.send(text_data=json.dumps({
            "type": "error",
            "data": {"message": message, "code": code}
        }))
    
    async def accept_invitation(self, invitation_id):
        try:
            # 초대 정보 가져오기
            invitation = await self.get_invitation_by_id(invitation_id)
            invitation.status = "accepted"
            await sync_to_async(invitation.save)()

            # 관련 초대 삭제
            await self.delete_other_invitations(invitation)

            # 친구 그룹 채널 생성
            group_name = await self.make_friend_group_channel(invitation)

            # 친구 그룹 알림 전송
            await self.channel_layer.group_send(
                group_name,
                {
                    "type": "invitation_accepted",
                    "data": {
                        "invitation_id": invitation.id,
                        "sender_id": invitation.sender.student_number,
                        "receiver_id": invitation.receiver.student_number,
                        "group_name": group_name,
                    },
                },
            )
        except InvitationRequest.DoesNotExist:
            await self.send_error("Invitation not found", 404)
        except Exception as e:
            print(f"Error accepting invitation: {e}")
            await self.send_error(f"Failed to accept invitation: {str(e)}", 500)
    
    async def get_invitation_by_id(self, invitation_id):
        """초대 정보를 ID로 가져옴."""
        return await sync_to_async(InvitationRequest.objects.get)(id=invitation_id)

    async def delete_other_invitations(self, invitation):
        """다른 초대 삭제."""
        await sync_to_async(
            lambda: InvitationRequest.objects.filter(sender=invitation.sender)
            .exclude(id=invitation.id)
            .delete()
        )()
        await sync_to_async(
            lambda: InvitationRequest.objects.filter(receiver=invitation.receiver)
            .exclude(id=invitation.id)
            .delete()
        )()
    
    async def make_friend_group_channel(self, invitation):
        """친구 그룹 채널 생성 및 등록."""
        try:
            sender = await sync_to_async(lambda: invitation.sender)()
            receiver = await sync_to_async(lambda: invitation.receiver)()
            group_name = f"friend_group_{sender.student_number}_{receiver.student_number}"

            # 그룹 이름 저장
            invitation.friend_group_channel = group_name
            await sync_to_async(invitation.save)()

            # 송신자와 수신자 그룹 추가
            await self.add_user_to_group(sender, group_name)
            await self.add_user_to_group(receiver, group_name)

            return group_name
        except Exception as e:
            print(f"Error in make_friend_group_channel: {e}")
            raise e
        
    async def invitation_accepted(self, event):
        data = event["data"]
        await self.send(text_data=json.dumps({
            "type": "invitation_accepted",
            "data": data
        }))

    async def add_user_to_group(self, user, group_name):
        """유저를 그룹에 추가."""
        if user.channel_name:
            await self.channel_layer.group_add(group_name, user.channel_name)
        else:
            print(f"User '{user.student_number}' has no channel_name")

    async def reject_invitation(self, invitation_id):
        try:
            # 초대 정보 가져오기
            invitation = await self.get_invitation_by_id(invitation_id)

            # 초대 상태를 거절로 변경
            await self.update_invitation_status(invitation, "rejected")

            # 클라이언트에게 거절 메시지 전송
            await self.send_response("invitation_rejected", {"invitation_id": invitation_id})

            # 송신자에게 알림 전송
            await self.send_rejection_to_sender(invitation)

            # 초대 삭제
            await sync_to_async(invitation.delete)()

        except InvitationRequest.DoesNotExist:
            await self.send_error("Invitation not found", 404)
        except Exception as e:
            print(f"Error rejecting invitation: {e}")
            await self.send_error(f"Failed to reject invitation: {str(e)}", 500)
        
    async def invitation_rejected(self, event):
        data = event["data"]
        await self.send(text_data=json.dumps({
            "type": "invitation_rejected",
            "data": data
        }))
        
    async def update_invitation_status(self, invitation, status):
        """초대 상태를 업데이트."""
        invitation.status = status
        await sync_to_async(invitation.save)()
        print(f"Invitation status updated to: {status}")

    async def send_rejection_to_sender(self, invitation):
        """송신자에게 초대 거절 알림을 전송."""
        sender = await sync_to_async(lambda: invitation.sender)()
        receiver = await sync_to_async(lambda: invitation.receiver)()
        await self.channel_layer.group_send(
            f"user_{invitation.sender.student_number}",
            {
                "type": "invitation_rejected",
                "data": {
                    "invitation_id": invitation.id,
                    "sender_id": sender.student_number,
                    "receiver_id": receiver.student_number,
                },
            },
        )