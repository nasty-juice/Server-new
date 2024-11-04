from django.db import models
from my_app.models import CustomUser
# Create your models here.

class MatchingQueue(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.user.username
    
class UserGroup(models.Model):
    users = models.ManyToManyField(CustomUser, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f'Group {self.id}'
