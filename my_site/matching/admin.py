from django.contrib import admin
from .models import MatchingQueue, MatchRequest
from my_app.models import CustomUser
# Register your models here.

#큐에 있는 유저만 표시하기 위한 클래스
class MatchingQueueAdmin(admin.ModelAdmin):
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "users":  # manytomany field의 이름
            if request.resolver_match.kwargs.get('object_id'):
                matching_queue = MatchingQueue.objects.get(id=request.resolver_match.kwargs['object_id'])
                kwargs["queryset"] = CustomUser.objects.filter(queue=matching_queue)
            else:
                kwargs["queryset"] = CustomUser.objects.none()
        
        return super().formfield_for_manytomany(db_field, request, **kwargs)

@admin.register(MatchRequest)
class MatchRequestAdmin(admin.ModelAdmin):
    list_display = ('location_name', 'created_at')
    search_fields = ('location_name',)
    filter_horizontal = ('confirm_users',)
    
admin.site.register(MatchingQueue, MatchingQueueAdmin)