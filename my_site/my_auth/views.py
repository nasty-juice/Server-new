from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView, View, FormView

from .forms import StudentCardForm
from .utils import perform_ocr, get_unknown_fields
from my_app.models import CustomUser
import os
from django.core.files.base import ContentFile

# Create your views here.
def initial_auth_view(request):
    return render(request, 'my_auth/initial_auth_view.html')

class StudentCardAuthView(FormView):
    model = CustomUser
    form_class = StudentCardForm
    template_name = 'my_auth/student_card_auth_view.html'
    success_url = reverse_lazy('my_auth:initial_auth_view')
    
    def form_valid(self, form):
        print("Form is valid")
        user = self.request.user  # 현재 로그인한 사용자
        print(f"Current user: {user}")

        try:
            student_card_image = form.cleaned_data.get('student_card_image')
            print("Student card image retrieved from form")

            # 이미지가 없을 경우 form_invalid 호출
            if not student_card_image:
                print("No student card image found")
                return self.form_invalid(form)

            # Save the student card image to the user model with a new filename

            # Generate a new filename
            new_filename = f"{user.student_number}_student_card.jpg"
            print(f"New filename: {new_filename}")

            # Save the image with the new filename
            if not user.student_card_image:
                user.student_card_image.save(new_filename, ContentFile(student_card_image.read()), save=False)
                print("Student card image saved to user with new filename")
            else:
                form.add_error('student_card_image', 'You have already uploaded a student card image.')
                return self.form_invalid(form)
            
            # clean_dict = perform_ocr(student_card_image)  # 변환된 이미지를 OCR 함수로 전달
            # print(f"OCR result: {clean_dict}")
            
            # unknown_fields = get_unknown_fields(clean_dict)
            # if unknown_fields:
            #     print(f"Unknown fields found: {unknown_fields}")
            #     form.add_error(None, f"학생증 인식에 실패한 항목: {', '.join(unknown_fields)}")
            #     return self.form_invalid(form)
            
            # user.student_card_data = clean_dict
            # print("Student card data saved to user")

            user.save()
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