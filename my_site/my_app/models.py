from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
import os
from .storages import PrivateMediaStorage

def user_directory_path(instance, filename):
    return os.path.join(settings.PRIVATE_MEDIA_ROOT, filename)

class CustomUser(AbstractUser):
    # Override the default User model
    first_name = None
    last_name = None
    
    username = models.CharField(max_length=20, unique=False, blank=False, null=False)
    
    email = models.EmailField(unique=True, blank=False, null=False)
    
    # Add additional fields here if needed
    student_number = models.CharField(max_length=8, unique=True, blank=False, null=False)
    
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.UUIDField(default=uuid.uuid4, unique=True)
    
    student_card_image = models.ImageField(storage=PrivateMediaStorage() ,upload_to = 'student_cards/', blank=True, null=True)
    student_card_data = models.JSONField(blank=True, null=True, default=dict)

    
    is_waiting = models.BooleanField(default=False)
    is_valid_student = models.BooleanField(default=False)
    
    USERNAME_FIELD = 'email' # This field must be unique
    
    REQUIRED_FIELDS = ['username', 'password'] # Used in createsuperuser command

    def save(self, *args, **kwargs):
        if self.student_card_image:
            self.student_card_image.storage.location = settings.PRIVATE_MEDIA_ROOT
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.email