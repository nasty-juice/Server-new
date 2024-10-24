from django import forms
from my_app.models import CustomUser
from allauth.account.forms import SignupForm
from django.contrib.auth.forms import UserCreationForm
from .validators import validate_school_email

class StudentCardForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['student_card_image']

# def get_signup_form():
#     from allauth.account.forms import SignupForm
#     return SignupForm

class CustomUserCreationForm(UserCreationForm, SignupForm):
    email = forms.EmailField(validators=[validate_school_email])
    student_card_form = StudentCardForm()

    class Meta:
        model = CustomUser
        fields = (
            'username',
            'student_number',
            'email',
            'password1',
            'password2',
            'student_card_image',
        )

    def signup(self, request, user):
        user.student_number = self.cleaned_data['student_number']
        user.student_card_image = self.cleaned_data['student_card_image']
        user.save()
        return user

    # def __init__(self, *args, **kwargs):
    #     SignupForm = get_signup_form()
    #     super(SignupForm, self).__init__(*args, **kwargs)