from django import forms
from my_app.models import CustomUser
from allauth.account.forms import SignupForm
from .validators import validate_school_email

# class StudentCardForm(forms.ModelForm):
#     class Meta:
#         model = CustomUser
#         fields = ['student_card_image']

class CustomUserCreationForm(SignupForm):
    email = forms.EmailField(validators=[validate_school_email])

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

    def save(self, request):
        user = super(CustomUserCreationForm, self).save(request)
        user.student_number = self.cleaned_data['student_number']
        user.student_card_image = self.cleaned_data['student_card_image']
        user.save()
        return user
