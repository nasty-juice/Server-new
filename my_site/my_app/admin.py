from django.contrib import admin
from .models import CustomUser
from django.utils.html import format_html
from django.conf import settings
from django import forms

from my_app.forms import AdminImageWidget

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

admin.site.register(CustomUser, CustomUserAdmin)
