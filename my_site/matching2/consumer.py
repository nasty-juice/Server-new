from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from redis import asyncio as aioredis
from asgiref.sync import sync_to_async

from django.utils import timezone
from django.conf import settings

from matching.models import MatchingQueue
from my_app.models import CustomUser
from .models import InvitationRequest, FriendGroup
from chat.models import ChatRoom
from .utils import get_user_in_queue, Timer
from .match import match

import json
import asyncio
import logging
import uuid

logger = logging.getLogger(__name__)

class Matching(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set up Redis connection
        self.redis = aioredis.from_url("redis://localhost")
        self.unique_channel_name = None
    #연결 확인
    async def connect(self):
        self.user = self.scope["user"]

        #  익명 사용자인 경우 연결 거부
        if self.user.is_anonymous:
            return
        
        # CustomUser 모델에 channel_name 저장
        self.user.channel_name = self.channel_name
        await sync_to_async(self.user.save)()

        # self.room_group_name = None

        # 유저의 고유 채널 이름 생성
        self.unique_channel_name = f"user_{self.user.student_number}"
        # print(self.unique_channel_name)
        await self.channel_layer.group_add(
            self.unique_channel_name,
            self.channel_name
        )
        
        # 페이지 이름 가져오기
        self.current_page = None            
        
        await self.accept()
        
    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            action = text_data_json.get("action")
            print(f"<{self.user.student_number}> : {action}")
            if not action:
                await self.send_error("Invalid action", 400)
                return
            
            match action:
                case "join_meal_page":
                    self.current_page = "meal_page"
                    # print("Joined meal page")
                    asyncio.create_task(self.broadcast_meal_status())
                    await self.send_response("join_meal_page", {})

                case "join_taxi_page":
                    self.current_page = "taxi_page"
                    asyncio.create_task(self.broadcast_taxi_status())
                    await self.send_response("join_taxi_page", {})
                
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
                
                case "start_matching":
                    location = text_data_json.get("location")
                    await self.start_matching(location)
                    await self.send_response("start_matching", {})
                case "disconnect":
                    await self.disconnect(1000)
                case "accept_match":
                    await match(self).accept_match()
                case "reject_match":
                    await match(self).reject_match()
                # 매칭 대기화면에서 취소한 경우
                case "cancel_matching":
                    await match(self).cancel_matching()
                case "confirm_start":
                    await match(self).connect_new_group(text_data_json.get("new_group_name"))
                    print(f"{self.user.student_number} -> {text_data_json.get('new_group_name')}")
                    
                case _:
                    await self.send_error("Invalid action", 400)
        except Exception as e:
            await self.send_error(f"Unhandled error: {str(e)}", 500)
    
    async def broadcast_meal_status(self):
        """학식 대기 상태를 주기적으로 클라이언트에 전송"""
        while self.current_page == "meal_page":
            meal_data = await self.get_meal_waiting_status()
            await self.send_response("meal_status", meal_data)
            await asyncio.sleep(5)  # 5초 간격으로 전송

    async def broadcast_taxi_status(self):
        # """택시 대기 상태를 주기적으로 클라이언트에 전송"""
        while self.current_page == "taxi_page":
            taxi_data = await self.get_taxi_waiting_status()
            await self.send_response("taxi_status", taxi_data)
            await asyncio.sleep(5)
    
    async def disconnect(self, close_code):
        try:
            # 그룹에서 사용자 제거
            if self.unique_channel_name:
                await self.channel_layer.group_discard(self.unique_channel_name, self.channel_name)
                print(f"Disconnected from group: {self.unique_channel_name}")

            # 초대 상태 확인 및 처리
            try:
                
                # 사용자한테 초대장이 있으면 초대장 상태 cancelled 변경 후 초대장 삭제                
                @sync_to_async
                def get_user_invitations(user):
                    # sender_invites와 receiver_invites를 통해 초대 데이터 가져오기
                    sent_invitations = list(InvitationRequest.objects.filter(sender=user))
                    received_invitations = list(InvitationRequest.objects.filter(receiver=user))
                    return sent_invitations + received_invitations

                # 초대 데이터를 가져옴
                invitations = await get_user_invitations(self.user)
                print(f"Found {len(invitations)} invitations for user {self.user.student_number}")

                if invitations:
                    for invitation in invitations:
                        # 초대 상태를 'cancelled'로 변경
                        await self.update_invitation_status(invitation, "cancelled")
                        print(f"Invitation ID {invitation.id} status updated to: cancelled")
                        # 송신자와 수신자에게 초대 취소 알림 전송
                        await self.notify_invitation_cancelled(invitation)
                        print(f"Sent cancellation notification for invitation ID {invitation.id}")
                        # 초대 삭제
                        await sync_to_async(invitation.delete)()
                        print(f"Invitation deleted")

                    print(f"All invitations for user {self.user.student_number} have been cancelled and deleted.")
            except Exception as e:
                print(f"Error handling invitations during disconnect: {e}")

            # working on when friend disconnects from the group
            try:
                # 사용자가 속한 모든 그룹 가져오기
                friend_groups = await sync_to_async(list)(FriendGroup.objects.filter(users=self.user))
                print(f"Found {len(friend_groups)} friend groups")
                
                # 그룹 내 사용자 제거 및 그룹 삭제 처리
                for friend_group in friend_groups:
                    # 그룹 내에 사용자가 포함된 경우 확인
                    user_in_group = await sync_to_async(friend_group.users.filter(id=self.user.id).exists)()
                    if user_in_group:
                        print(f"User {self.user.student_number} is in friend group: {friend_group.name}")
                        self.channel_layer.group_send(
                            friend_group.friend_group_channel,
                            {
                                "type": "user_disconnected",
                                "data": {
                                    "disconnected_user": self.user.student_number,
                                    "message": "User has disconnected.",
                                },
                            },
                        )
                        await sync_to_async(friend_group.delete)()
                    else:
                        print(f"User {self.user.student_number} is not in friend group: {friend_group.name}")
            except Exception as e:
                # 예외 처리
                print(f"Error handling friend group during disconnect: {e}")
                        
            
            # Redis 키 삭제 및 연결 종료
            try:
                await self.redis.delete(self.unique_channel_name)
                print(f"Redis key deleted for: {self.unique_channel_name}")
            except Exception as redis_error:
                print(f"Error deleting Redis key: {redis_error}")
            finally:
                await self.redis.aclose()
                print("Redis connection closed.")

        except Exception as e:
            print(f"Error during disconnect: {e}")

    async def update_invitation_status(self, invitation, status):
        """초대 상태를 업데이트."""
        invitation.status = status
        await sync_to_async(invitation.save)()
        # print(f"Invitation ID {invitation.id} status updated to: {status}")

    async def notify_invitation_cancelled(self, invitation):
        """송신자와 수신자에게 초대 취소 알림 전송."""
        sender = await sync_to_async(lambda: invitation.sender)()
        receiver = await sync_to_async(lambda: invitation.receiver)()

        group_name = await sync_to_async(lambda: invitation.friend_group_channel)()
        if group_name:
            await self.channel_layer.group_send(
                group_name,
                {
                    "type": "invitation_cancelled",
                    "data": {
                        "invitation_id": invitation.id,
                        "sender_id": sender.student_number,
                        "receiver_id": receiver.student_number,
                        "message": "Invitation has been cancelled. Friend disconnected.",
                    },
                },
            )
        else:
            print(f"No group_name for invitation ID {invitation.id}")

        # print(f"Cancellation notification sent for invitation ID {invitation.id}")

    async def invitation_cancelled(self, event):
        """초대 취소 이벤트 처리."""
        data = event["data"]
        await self.send(text_data=json.dumps({
            "type": "invitation_cancelled",
            "data": data
        }))
        print(f"Sent cancellation notification for invitation ID {data['invitation_id']}")

    async def user_disconnected(self, event):
        """사용자 연결 해제 이벤트 처리."""
        data = event["data"]
        await self.send(text_data=json.dumps({
            "type": "user_disconnected",
            "data": data
        }))
        print(f"Sent user disconnected notification for user {data['disconnected_user']}")

    async def get_meal_waiting_status(self):
        RESTAURANT_LIST = ['student_center', 'myeongjin', 'staff_cafeteria', 'welfare']
        meal_queues = await database_sync_to_async(list)(
            MatchingQueue.objects.filter(location__in=RESTAURANT_LIST)
        )

        response_data = {name: 0 for name in RESTAURANT_LIST}
        location_user_counts = {name: [] for name in RESTAURANT_LIST}

        for queue in meal_queues:
            groups = await sync_to_async(list)(queue.groups.all())
            total_user_count = 0
            for group in groups:
                user_count = await database_sync_to_async(group.users.count)()
                total_user_count += user_count
            location_user_counts[queue.location].append(total_user_count)
            # print(f"Queue {queue.name} at {queue.location} has {total_user_count} users")

        for location, counts in location_user_counts.items():
            if counts:
                response_data[location] = max(counts)
                # print(f"Location {location} has max user count: {response_data[location]}")

        return response_data

    async def get_taxi_waiting_status(self):
        ROUTE_LIST = ['station_to_mju', 'mju_to_station']
        meal_queues = await database_sync_to_async(list)(
            MatchingQueue.objects.filter(location__in=ROUTE_LIST)
        )

        response_data = {name: 0 for name in ROUTE_LIST}
        location_user_counts = {name: [] for name in ROUTE_LIST}

        for queue in meal_queues:
            groups = await sync_to_async(list)(queue.groups.all())
            total_user_count = 0
            for group in groups:
                user_count = await database_sync_to_async(group.users.count)()
                total_user_count += user_count
            location_user_counts[queue.location].append(total_user_count)
            # print(f"Queue {queue.name} at {queue.location} has {total_user_count} users")

        for location, counts in location_user_counts.items():
            if counts:
                response_data[location] = max(counts)
                # print(f"Location {location} has max user count: {response_data[location]}")

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
            await self.check_both_existing_invitations(self.user, friend)

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
                "sender": {
                    "name": self.user.username,
                    "id": self.user.student_number,
                }
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

    async def check_existing_invitations(self, user):
        """Check for existing invitations."""
        if await sync_to_async(self.user.sent_invites.exists)():
            print("You have invitation.")
            return True
        
        if await sync_to_async(self.user.received_invites.exists)():
            print("You have invitation.")
            return True
        return False

    async def check_both_existing_invitations(self, user, friend):
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
            invitation = await self.get_invitation_by_id(invitation_id)
            if invitation.status == "pending":
                await self.reject_invitation(invitation_id)
                print(f"Auto-rejected invitation: {invitation_id}")
        except Exception as e:
            print(f"Error auto-rejecting invitation: {e}")

    async def send_invitation(self, event):
        invitation_id = event["invitation_id"]
        sender = event["sender"]
        await self.send(text_data=json.dumps({
            "type": "invitation",
            "data": {
                "invitation_id": invitation_id,
                "name": sender["name"],
                "number": sender["id"],
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
            
            sender = await sync_to_async(lambda: invitation.sender)()
            receiver = await sync_to_async(lambda: invitation.receiver)()
            
            await sync_to_async(sender.invitation.add)(invitation)
            await sync_to_async(receiver.invitation.add)(invitation)
            

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
                        "sender": {
                            "id": invitation.sender.student_number,
                            "name": invitation.sender.username,
                            "department": invitation.sender.department,
                            "temperature": str(invitation.sender.temperature),
                        },
                        "receiver": {
                            "id": invitation.receiver.student_number,
                            "name": invitation.receiver.username,
                            "department": invitation.receiver.department,
                            "temperature": str(invitation.receiver.temperature),
                        },    
                        "group_name": group_name,
                    },
                },
            )
        except InvitationRequest.DoesNotExist:
            await self.send_error("Invitation not found", 404)
        except Exception as e:
            # print(f"Error accepting invitation: {e}")
            logger.error(f"Error accepting invitation: {e}")
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

    @database_sync_to_async
    def get_invitation(self):
        invitation = self.user.invitation.first()
        print(invitation)
        return invitation

    async def start_matching(self, loc):
        # 초대장이 있는지 확인
        # 초대장 있으면 duo_match
        
        if await self.check_existing_invitations(self.user):
            #만약에 초대장 받은 사람이면 return
            #재훈
            # if await sync_to_async(self.user.invitation.receiver)() == self.user:
            #     return
            
            await self.send_response("duo_match", {})
            print("Duo match start") 

            invitation = await self.get_invitation()

            if invitation.receiver == self.user:
                print("YOU ARE RECEIVER. CANNOT START MATCHING")
                await self.send_error("You are receiver. Cannot start matching", 400)
                return
        
            print(invitation.friend_group_channel)
            
            duo_group = await sync_to_async(FriendGroup.objects.create)(
                name = f"duo_{invitation.friend_group_channel}",
                status = "duo",
                location = loc,
                created_at = timezone.now(),
                friend_group_channel = invitation.friend_group_channel,
            )
            
            sender = await sync_to_async(lambda: invitation.sender)()
            receiver = await sync_to_async(lambda: invitation.receiver)()
            await sync_to_async(duo_group.users.add)(sender)
            await sync_to_async(duo_group.users.add)(receiver)
            await sync_to_async(duo_group.save)()
            print(f"Duo group created: {duo_group.name}")
            await self.get_or_create_queue(duo_group)
            
        # 초대장이 없으면 solo_match
        else:
            await self.send_response("solo_match", {})
            # 솔로 그룹 생성
            print("0")
            solo_group = await sync_to_async(FriendGroup.objects.create)(
                name = f"solo_{self.user.student_number}",
                status = "solo",
                location = loc,
                created_at = timezone.now(),
            )
            print("1")
            await sync_to_async(solo_group.users.add)(self.user)
            print("2")
            await self.get_or_create_queue(solo_group)

    async def get_or_create_queue(self, group):
        print("3")
        # location에 해당하는 현재 대기열 targetQueueList 가져오기
        targetQueueList = await database_sync_to_async(list)(MatchingQueue.objects.filter(location=group.location))
        print("4")
        print(targetQueueList)
        
        # 현재 매칭 시작하기를 누른 그룹 안의 유저 수 세기
        usernum_in_group = await sync_to_async(group.users.count)()
        print(f"User number in group: {usernum_in_group}")
        
        group_added = False
        joined_queue = None
        
        # 대기열이 존재하지 않는 경우 대기열 생성
        if not targetQueueList:
            print("5")
            newQueue = await sync_to_async(MatchingQueue.objects.create)(
                name = f"{group.location}_{uuid.uuid4()}",
                location = group.location,
                created_at = timezone.now(),
            )
            await sync_to_async(newQueue.groups.add)(group)
            group_added = True
            self.room_group_name = newQueue.name
            joined_queue = newQueue
        # 대기열이 이미 존재하는 경우
        else:
            print("6")

            # 대기열 리스트 순회
            for queue in targetQueueList:
                print(f"Queue: {queue.name}")

                current_usernum_in_queue = 0
                
                # queue에 연결된 모든 groups 가져오기
                groups = await sync_to_async(list)(queue.groups.all())
                
                for grp in groups:
                    print(f"  Group: {grp.name}")
                    # group에 연결된 모든 users 가져오기
                    users = await sync_to_async(list)(grp.users.all())
                    print(f"    Users: {[user.username for user in users]}")

                    current_usernum_in_queue += len(users)
                    print(f"    Users count: {current_usernum_in_queue}")
                    
                # 현재 대기열에 들어갈 공간이 있다.
                if current_usernum_in_queue + usernum_in_group <= settings.MAX_Q_SIZE:
                    await sync_to_async(queue.groups.add)(group)
                    group_added = True
                    self.room_group_name = queue.name
                    joined_queue = queue
                    
                    print(f"    Group added to queue: {group.name}")
                    # 큐에 추가 후 채팅방으로 빼주는 로직
                    break
                # 없다.
                else:
                    print(f"    Group not added to queue: {group.name}")
                    continue
            
            if not group_added:
                # 모든 대기열을 확인했는데도 대기열에 들어갈 공간이 없다.
                newQueue = await sync_to_async(MatchingQueue.objects.create)(
                    name = f"{group.location}_{uuid.uuid4()}",
                    location = group.location,
                    created_at = timezone.now(),
                )
                await sync_to_async(newQueue.groups.add)(group)
                group_added = True
                self.room_group_name = newQueue.name 
                joined_queue = newQueue
                
                print(f"Queue created: {newQueue}")
                # 큐에 추가 후 채팅방으로 빼주는 로직
        
        if group_added:
            if group.status == "duo":
                invitation = await self.get_invitation()
                print(f"invitation : {invitation}")
                receiver = await sync_to_async(lambda: invitation.receiver)()
                print(f"receiver : {receiver.username}")
                #수신자 그룹 추가
                #B한테 self.room_group_name 최신화
                group_name = await sync_to_async(lambda: invitation.friend_group_channel)()
                print(f"group_name : {group_name}")
                
                await self.channel_layer.group_send(
                    group_name,
                    {
                        "type": "send_to_group",
                        "message": self.room_group_name,
                        "status": "start_matching"
                    }
                )
                
                await self.add_user_to_group(receiver, self.room_group_name)
            

                
            
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.send_waiting_status_in_loading(joined_queue)


        targetQueueList = await database_sync_to_async(list)(MatchingQueue.objects.filter(location=group.location))
        
        for queue in targetQueueList:
            print(f"Queue: {queue.name}")

            current_usernum_in_queue = 0
            
            # queue에 연결된 모든 groups 가져오기
            groups = await sync_to_async(list)(queue.groups.all())
            
            for grp in groups:
                print(f"  Group: {grp.name}")
                # group에 연결된 모든 users 가져오기
                users = await sync_to_async(list)(grp.users.all())
                print(f"    Users: {[user.username for user in users]}")

                current_usernum_in_queue += len(users)
                print(f"    Users count: {current_usernum_in_queue}")
            
            print(f"Current queue size: {current_usernum_in_queue}")
            
            print(f"MAX_Q_SIZE : {settings.MAX_Q_SIZE}")
            
            if current_usernum_in_queue == settings.MAX_Q_SIZE:
                await self.ask_member_to_join_room(queue)
                break
                
    async def ask_member_to_join_room(self,targetQuque):
        userData = await get_user_in_queue(targetQuque)
        # queue 채널 그룹에 연결된 모든 유저한테 메시지 전송
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "ask_join_room",
                "message": userData,
                "status": "matched",
            }
        )
        
        asyncio.create_task(Timer(self,targetQuque).send_timer())
        
    async def ask_join_room(self, event):
        message = event["message"]
        # await self.send_response("ask_join_room", {"message": message})
        await self.send(text_data=json.dumps({
            "type": "ask_join_room",
            "message": message,
        }))
     
    async def send_to_group(self, event):
        response = {
            "status": event['status'],
            "message": event['message'],
        }
        try:
            await self.send(text_data=json.dumps(response))
        except Exception as e:
            print(f"타이머 메시지 전송 중 오류 발생: {e}")
            return
    

    async def send_waiting_status_in_loading(self, joined_queue):
        user_num = 0
        groups = await sync_to_async(list)(joined_queue.groups.all())
        for group in groups:
            temp = await sync_to_async(list)(group.users.all())
            num = len(temp)
            user_num += num
            
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "send_to_group",
                "message": user_num,
                "status": "waiting_status"
            }
        )