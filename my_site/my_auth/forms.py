from django import forms
from django.db import transaction
from my_app.models import CustomUser
from allauth.account.forms import SignupForm
from .validators import validate_school_email, validate_image_extension

class CustomSignupForm(SignupForm):
    
    student_number = forms.CharField(required=True, max_length=8)
    student_card_image = forms.ImageField(required=True, validators=[validate_image_extension])

    class Meta:
        model = CustomUser
        fields = ['username', 'student_number', 'email', 'password1', 'password2', 'student_card_image']

    def clean_student_number(self):
        student_number = self.cleaned_data['student_number']
        if CustomUser.objects.filter(student_number=student_number).exists():
            raise forms.ValidationError('이미 등록된 학번입니다.')
        return student_number
        
        
    def save(self, request, commit=True):
        with transaction.atomic():
            user = super(CustomSignupForm, self).save(request)
            # 추가적인 사용자 저장 로직 (필요 시)
            user.student_number = self.cleaned_data['student_number']
            user.student_card_image = self.cleaned_data['student_card_image']
            
            if commit:
                user.save()
        
        return user
   