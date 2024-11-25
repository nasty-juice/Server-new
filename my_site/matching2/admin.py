from django.contrib import admin
from .models import InvitationRequest, FriendGroup

# Register your models here.
class FriendGroupAdmin(admin.ModelAdmin):
    
    list_display = ('name', 'created_at')
    filter_horizontal = ('users',)
    
admin.site.register(InvitationRequest)
admin.site.register(FriendGroup, FriendGroupAdmin)