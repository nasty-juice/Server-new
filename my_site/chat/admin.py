from django.contrib import admin
from .models import ChatRoom, ChatMessage
# Register your models here.

class ChatmessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    fields = ('user', 'message', 'created_at')
    readonly_fields = ('created_at','message')

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    inlines = [ChatmessageInline]
    list_display = ('name', 'created_at')