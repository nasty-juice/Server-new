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
    name = models.CharField(max_length=100, unique=True, null=True, blank=True)
    users = models.ManyToManyField(CustomUser, related_name='users',blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    location = models.CharField(
        max_length=100,
        choices=(
            ("myeongjin", "명진당"),
            ("student_center", "학생회관"),
            ("staff_cafeteria", "교직원식당"),
            ("welfare", "복지동"), 
            ("station_to_mju", "기흥 -> 명지대"),
            ("mju_to_station", "명지대 -> 기흥"),
            ("none", "None"),
        ),
        default="none",
        blank=True,
        null=True,
    )
    friend_group_channel = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=(
            ("solo", "Solo"),
            ("duo", "Duo"),
            ("none", "None"),
            
        ),
        default="none",
        null=True,
        blank=True,
    )
    

    def __str__(self):
        return f"{self.name} - {self.location}"