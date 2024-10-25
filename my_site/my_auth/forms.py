from typing import OrderedDict
from django import forms
from my_app.models import CustomUser
from django.contrib.auth.forms import UserCreationForm
from allauth.account.forms import SignupForm
from .validators import validate_school_email

class CustomUserCreationForm(UserCreationForm, SignupForm):
    def __init__(self, *args, **kwargs):
        UserCreationForm.__init__(self, *args, **kwargs)  # Django 기본 사용자 생성 폼 초기화
        SignupForm.__init__(self, *args, **kwargs)        # 추가 기능을 위한 SignupForm 초기화

        # 필드 순서 변경
        self.fields = OrderedDict([
            ('username', self.fields['username']),
            ('student_number', self.fields['student_number']),
            ('email', self.fields['email']),
            ('password1', self.fields['password1']),
            ('password2', self.fields['password2']),
        ])

        
    email = forms.EmailField(validators=[validate_school_email])

    class Meta:
        model = CustomUser
        fields = (
            'username',
            'student_number',
            'email',
            'password1',
            'password2',
            # 'student_card_image',
        )

    def save(self, request):
        # UserCreationForm의 save 메서드를 먼저 호출하여 사용자 객체 생성 (commit=False로 저장 중간 처리)
        # UserCreationForm의 save 메서드는 사용자 객체를 반환하므로 이를 user 변수에 저장
        # UserCreationForm 은 email, username, password를 저장하므로 이후에 추가로 필요한 데이터를 저장
        user = super(UserCreationForm, self).save(commit=False)
        
        # SignupForm에서 필요한 추가 처리나 로직이 있다면 request를 전달하여 추가
        user.student_number = self.cleaned_data.get('student_number')
        
        # 추가로 필요한 모든 필드를 저장한 후 최종 저장
        user.save()

        # SignupForm의 추가 저장 로직을 처리 (예: 이메일 인증, 사용자 추가 처리 등)
        # self.save_m2m()  # Many-to-Many 필드가 있을 경우 M2M 데이터를 저장

        return user

class StudentCardForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['student_card_image']
        