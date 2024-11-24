from django.db import models
from my_app.models import CustomUser
# Create your models here.
class InvitationRequest(models.Model):
    sender = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE, 
        related_name="sent_invites",
        null=True,
        blank=True
    )
    receiver = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name="received_invites",
        null=True,
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=(
            ("pending", "Pending"),
            ("accepted", "Accepted"),
            ("rejected", "Rejected"),
            ("cancelled", "Cancelled"),
        ),
        default="pending"
    )  # 초대 상태

    friend_group_channel = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.sender} -> {self.receiver} ({self.status})"
    
class FriendGroup(models.Model):
    name = models.CharField(max_length=100)
    users = models.ManyToManyField(CustomUser, related_name='friend_group',blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name