from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from .models import FriendGroup

@receiver(m2m_changed, sender=FriendGroup.users.through)
def debug_users_change(sender, instance, action, **kwargs):
    print(f"Action: {action}, Users: {instance.users.all()}")
