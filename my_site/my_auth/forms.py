from django import forms
from my_app.models import CustomUser
from allauth.account.forms import SignupForm
from .validators import validate_school_email, validate_image_extension

class CustomSignupForm(SignupForm):
    
    student_number = forms.CharField(required=True, max_length=8)
    student_card_image = forms.ImageField(required=True, validators=[validate_image_extension])

    class Meta:
        model = CustomUser
        fields = ['username', 'student_number', 'email', 'password1', 'password2', 'student_card_image']
        
    def save(self, request):
        user = super(CustomSignupForm, self).save(request)
        # 추가적인 사용자 저장 로직 (필요 시)
        user.student_number = self.cleaned_data['student_number']
        user.student_card_image = self.cleaned_data['student_card_image']
        user.save()
        
        return user