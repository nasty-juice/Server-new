from django.db import models
from my_app.models import CustomUser
# Create your models here.

class MatchingQueue(models.Model):
    name = models.CharField(max_length=100)
    users = models.ManyToManyField(CustomUser, related_name='queue',blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class UserGroup(models.Model):
    name = models.CharField(max_length=100, blank=True)
    users = models.ManyToManyField(CustomUser, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f'Group {self.id}'
