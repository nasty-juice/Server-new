from django.contrib import admin
from .models import MatchingQueue, UserGroup
from my_app.models import CustomUser
# Register your models here.

#그룹에 있는 유저만 표시하기 위한 클래스
class UserGroupAdmin(admin.ModelAdmin):
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "users": # manytomany field의 이름
            if request.resolver_match.kwargs.get('object_id'):
                user_group = UserGroup.objects.get(id=request.resolver_match.kwargs['object_id'])
                kwargs["queryset"] = CustomUser.objects.filter(usergroup = user_group)
            else:
                kwargs["queryset"] = CustomUser.objects.none()
        
        return super().formfield_for_manytomany(db_field, request, **kwargs)
            

admin.site.register(MatchingQueue)
admin.site.register(UserGroup, UserGroupAdmin)