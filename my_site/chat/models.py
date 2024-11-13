from django.db import models

# Create your models here.
class ChatRoom(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    #유저 4명 데이터 넣기
    #users = models.ManyToManyField('my_app.CustomUser', related_name='rooms', blank=True)
    def __str__(self):
        return self.name

class ChatMessage(models.Model):
    chat_room = models.ForeignKey(ChatRoom, related_name='messages', on_delete=models.CASCADE)
    user = models.ForeignKey('my_app.CustomUser', on_delete=models.SET_NULL, null=True)
    
    message = models.BinaryField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user} : {self.message}"