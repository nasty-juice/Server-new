from asgiref.sync import sync_to_async
from matching.models import MatchingQueue, MatchRequest
from my_app.models import CustomUser
from .models import InvitationRequest, FriendGroup

import asyncio
import json

@sync_to_async
def get_user_in_queue(targetQueue):
    user_data = []
    for group in targetQueue.groups.all(): 
        for user in group.users.all():
            try:
                user_info = {
                    'user_number': user.student_number,
                    'user_temperature': float(user.temperature),
                }
                user_data.append(user_info)
            except Exception as e:
                print(f"유저 데이터 처리 중 오류 발생: {e}")
                continue
    
    return user_data

# 타이머 설정
class Timer():
    def __init__(self, consumer):
        self.consumer = consumer
    
    async def send_timer(self):
        for currTime in range(15, 0, -1):
            print("YOU")
            await self.consumer.channel_layer.group_send(
                self.consumer.room_group_name,
                {
                    "type": "send_to_group",
                    "message": currTime,
                    "status": "matchTimer",    
                },
            )
            await asyncio.sleep(1)

       
        await self.consumer.channel_layer.group_send(
            self.consumer.room_group_name,
            {
                "type": "send_to_group",
                "message": "timeOut",
                "status": "matchTimer",    
            },
        )

    
    
    
        