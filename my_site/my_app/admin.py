from django.contrib import admin
from django import forms

from my_app.forms import AdminImageWidget
from .models import CustomUser

class CustomUserAdminForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = '__all__'
        widgets = {
            'student_card_image': AdminImageWidget()
        }
        
class CustomUserAdmin(admin.ModelAdmin):
    
    form = CustomUserAdminForm
        
    list_display = ('id', 'email', 'student_number') 
    list_display_links = ('id', 'email') 
    
    search_fields = ('email', 'student_number')
    filter_horizontal = ('invitation',)
    
admin.site.register(CustomUser, CustomUserAdmin)
