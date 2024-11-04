from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView, View, FormView
from allauth.account.views import SignupView

from .utils import perform_ocr, get_unknown_fields
from my_app.models import CustomUser
import os
from django.core.files.base import ContentFile

from django.contrib.auth.decorators import login_required

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from allauth.account.utils import send_email_confirmation
from django.contrib.auth import get_user_model

from .forms import CustomSignupForm

# Create your views here.
@login_required
def signup_success_view(request):
    return render(request, 'my_auth/signup_success_view.html')

def langing_page(request):
    return render(request, 'my_auth/landing_page.html')


class CustomSignupView(SignupView):
    model = CustomUser
    form_class = CustomSignupForm
    
    def form_valid(self, form):
        print("Form is valid")
        
        user = form.save(commit=False)
        
        try:
            student_card_image = form.cleaned_data.get('student_card_image')
            print("Student card image retrieved from form")
            
            # 이미지가 없을 경우 form_invalid 호출
            if not student_card_image:
                print("No student card image found")
                return self.form_invalid(form)
            
            # Save the student card image to the user model with a new filename
            new_filename = f"{user.student_number}_student_card.jpg"
            print(f"New filename: {new_filename}")

            user.student_card_image.save(new_filename, ContentFile(student_card_image.read()), save=False)

            clean_dict = perform_ocr(student_card_image)  # 변환된 이미지를 OCR 함수로 전달
            print(f"OCR result: {clean_dict}")
            
            unknown_fields = get_unknown_fields(clean_dict)
            if unknown_fields:
                print(f"Unknown fields found: {unknown_fields}")
                form.add_error(None, f"학생증 인식에 실패한 항목: {', '.join(unknown_fields)}")
                return self.form_invalid(form)
            
            user.student_card_data = clean_dict
            user.save()
            print(user.student_card_image.name, user.student_card_image.path)
            print("User saved successfully")
            
            
        except Exception as e:
            print(f"Error during image processing: {e}")
            form.add_error('student_card_image', f'이미지 처리 중 오류가 발생했습니다: {e}')
            return self.form_invalid(form)

        return super().form_valid(form)
    
    def form_invalid(self, form):
        print("Form is invalid")
        response = super().form_invalid(form)
        response.status_code = 400
        return response


User = get_user_model()

class EmailVerificationView(APIView):
    def post(self, request):
        email = request.data.get("email")
        print(request.data)
        try:
            print(User)
            user = User.objects.get(email=email)
            print(user.student_number)
            send_email_confirmation(request, user)
            return Response({"message": "Verification email sent."}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

# class StudentCardAuthView(FormView):

#     model = CustomUser
#     form_class = StudentCardForm
#     template_name = 'my_auth/student_card_auth_view.html'
#     success_url = reverse_lazy('my_auth:signup_success_view')
    
#     def form_valid(self, form):
#         print("Form is valid")
#         user = self.request.user  # 현재 로그인한 사용자
#         print(f"Current user: {user}")

#         try:
#             student_card_image = form.cleaned_data.get('student_card_image')
#             print("Student card image retrieved from form")

#             # 이미지가 없을 경우 form_invalid 호출
#             if not student_card_image:
#                 print("No student card image found")
#                 return self.form_invalid(form)

#             # Save the student card image to the user model with a new filename
#             new_filename = f"{user.student_number}_student_card.jpg"
#             print(f"New filename: {new_filename}")

            
#             if not user.student_card_image:
#                 user.student_card_image.save(new_filename, ContentFile(student_card_image.read()), save=False)
#                 print("Student card image saved to user with new filename")
#             else:
#                 form.add_error('student_card_image', 'You have already uploaded a student card image.')
#                 return self.form_invalid(form)      

#             # print(type(student_card_image))

#             clean_dict = perform_ocr(student_card_image)  # 변환된 이미지를 OCR 함수로 전달
#             print(f"OCR result: {clean_dict}")
            
#             unknown_fields = get_unknown_fields(clean_dict)
#             if unknown_fields:
#                 print(f"Unknown fields found: {unknown_fields}")
#                 form.add_error(None, f"학생증 인식에 실패한 항목: {', '.join(unknown_fields)}")
#                 return self.form_invalid(form)
            
#             # user.student_card_data = clean_dict
#             # print("Student card data saved to user")
#             user.student_card_data = clean_dict
#             user.save()
#             print(user.student_card_image.name, user.student_card_image.path)
#             print("User saved successfully")

#         except Exception as e:
#             print(f"Error during image processing: {e}")
#             form.add_error('student_card_image', f'이미지 처리 중 오류가 발생했습니다: {e}')
#             return self.form_invalid(form)

#         return super().form_valid(form)
    
#     def form_invalid(self, form):
#         print("Form is invalid")
#         response = super().form_invalid(form)
#         response.status_code = 400
#         return response




