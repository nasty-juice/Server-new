from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from .chat_bot import chat_open_message, chat_send_time_message, delete_chat_room

# Create your models here.
class ChatRoom(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    #유저 4명 데이터
    #users = models.ManyToManyField('my_app.CustomUser', related_name='chat_rooms', blank=True)
    #온도 평가 데이터
    temperature_change_list = models.JSONField(default=list, blank=True)
    def __str__(self):
        return self.name

class ChatMessage(models.Model):
    chat_room = models.ForeignKey(ChatRoom, related_name='messages', on_delete=models.CASCADE, null=True)
    user = models.ForeignKey('my_app.CustomUser', on_delete=models.SET_NULL, null=True)
    message = models.BinaryField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_system = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user} : {self.message}"
    
@receiver(post_save, sender=ChatRoom)
def create_initial_chat_message(sender, instance, created, **kwargs):
    if created:
        chat_open_message(instance)
        delete_chat_room.apply_async((instance.id,), countdown=180)
        chat_send_time_message.apply_async((instance.id, "채팅방 종료까지 10분 남았습니다. 매너온도 평가 부탁드립니다."), countdown=150)