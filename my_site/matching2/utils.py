from asgiref.sync import sync_to_async
from matching.models import MatchingQueue, MatchRequest
from my_app.models import CustomUser
from .models import InvitationRequest

@sync_to_async
def get_or_create_queue(status):
    pass

