from django.test import TestCase
from .forms import CustomUserCreationForm
from my_app.models import CustomUser

# my_site/my_auth/test_forms.py


class CustomUserCreationFormTest(TestCase):

    def test_meta_attributes(self):
        form = CustomUserCreationForm()
        self.assertEqual(form._meta.model, CustomUser)
        self.assertEqual(
            form._meta.fields,
            (
                'username',
                'student_number',
                'email',
                'password1',
                'password2',
                'student_card_image',
            )
        )

if __name__ == '__main__':
    TestCase.main()