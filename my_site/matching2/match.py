from asgiref.sync import sync_to_async
from django.conf import settings

import asyncio
import json
import uuid

from matching.models import MatchingQueue
from .models import InvitationRequest
from chat.models import ChatRoom
from chat.chat_bot import chat_send_time_message

class match:
    def __init__(self, consumer):
        self.consumer = consumer
    
    async def accept_match(self):
        targetQueue = await sync_to_async(MatchingQueue.objects.get)(name=self.consumer.room_group_name)
        user_exist = await sync_to_async(lambda: targetQueue.confirmed_users.filter(id=self.consumer.user.id).exists())()
        print(f"match_request: {targetQueue.name}")
        if not user_exist:
            await sync_to_async(targetQueue.confirmed_users.add)(self.consumer.user)
            await sync_to_async(targetQueue.save)()
            await self.consumer.channel_layer.group_send(
                self.consumer.room_group_name,
                {
                    "type": "send_to_group",
                    "message": f"{self.consumer.user.student_number}",
                    "status": "accepted"
                }
            )
        else:
            await self.consumer.send(text_data=json.dumps({'status': 'error','message': 'already'}))
            return
        
        confirm_user_count = await sync_to_async(targetQueue.confirmed_users.count)()
        
        if confirm_user_count == settings.MAX_Q_SIZE:
            all_users = await sync_to_async(lambda: list(targetQueue.confirmed_users.all()))()
            chat_room_name = f"chat_{targetQueue.name}"
            chat_room = await sync_to_async(lambda: ChatRoom.objects.create(name=chat_room_name))()
        
            
            for user in all_users:
                await sync_to_async(lambda: user.sent_invites.all().delete())()
                
            await self.delete_all_friend_groups(targetQueue)
            await sync_to_async(targetQueue.delete)()
            
            #모든 사용자의 join_room 필드를 업데이트
            await self.update_users_join_room(all_users, chat_room)
            
            await self.consumer.channel_layer.group_send(
                self.consumer.room_group_name,
                {
                    "type": "send_to_group",
                    "message": chat_room_name,
                    "status": "confirmed"
                }
            )
            
            
            
    async def reject_match(self):
        targetQueue = await sync_to_async(MatchingQueue.objects.get)(name=self.consumer.room_group_name)
        await sync_to_async(targetQueue.confirmed_users.remove)(self.consumer.user)
        
        await self.consumer.channel_layer.group_send(
            self.consumer.room_group_name,
            {
                "type": "send_to_group",
                "message": f"{self.consumer.user.student_number}",
                "status": "rejected"
            }
        )
    async def connect_new_group(self, new_group_name):
        self.consumer.room_group_name = new_group_name
        
    @sync_to_async
    def update_users_join_room(self, all_users, chat_room):
        for user in all_users:
            user.join_room = chat_room
            user.save()
        
    async def delete_all_friend_groups(self, targetQueue):
        friend_groups = await sync_to_async(lambda: list(targetQueue.groups.all()))()
        for group in friend_groups:
            await sync_to_async(group.delete)()


    async def cancel_matching(self):
        targetQueue = await sync_to_async(MatchingQueue.objects.get)(name=self.consumer.room_group_name)
        targetFriendGroup = await sync_to_async(lambda: targetQueue.groups.get(users=self.consumer.user))()
        print(targetQueue)
        print(targetFriendGroup)
        print(targetFriendGroup.friend_group_channel)
        
        await sync_to_async(targetQueue.groups.remove)(targetFriendGroup)
        
        if targetFriendGroup.status == "solo":
            await self.consumer.send(text_data=json.dumps({'status': 'cancel_matching','message': 'solo'}))

        else:
            await self.consumer.channel_layer.group_send(
                targetFriendGroup.friend_group_channel,
                {
                    "type": "send_to_group",
                    "message": f"{self.consumer.user.student_number}",
                    "status": "cancel"
                }
            )

        await sync_to_async(targetFriendGroup.delete)()
        
        groups = await sync_to_async(lambda: list(targetQueue.groups.all()))()
        if len(groups) == 0:
            await sync_to_async(targetQueue.delete)()
            print("delete queue")
        