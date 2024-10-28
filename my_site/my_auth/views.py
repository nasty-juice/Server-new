from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView, View, FormView

from .forms import StudentCardForm
from .utils import perform_ocr, get_unknown_fields

from PIL import Image
import io



# Create your views here.
def initial_auth_view(request):
    return render(request, 'my_auth/initial_auth_view.html')

class StudentCardAuthView(FormView):
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
                

             # 이미지를 BytesIO로 변환 후 열기
            # 이미지를 BytesIO로 변환 후 열기
            try:
                image_data = student_card_image.read()  # 파일 데이터를 읽기
                if image_data is None:
                    form.add_error('student_card_image', "이미지 데이터를 읽을 수 없습니다.")
                    return self.form_invalid(form)
                
                image = Image.open(io.BytesIO(image_data))  # BytesIO로 변환 후 열기
                image.verify()  # 이미지 파일이 유효한지 검사
            except Exception as e:
                form.add_error('student_card_image', f"이미지 파일이 손상되었거나 지원되지 않는 형식입니다: {e}")
                return self.form_invalid(form)
            
            clean_dict = perform_ocr(image)  # 변환된 이미지를 OCR 함수로 전달
            print(f"OCR result: {clean_dict}")
            
            unknown_fields = get_unknown_fields(clean_dict)
            if unknown_fields:
                print(f"Unknown fields found: {unknown_fields}")
                form.add_error(None, f"학생증 인식에 실패한 항목: {', '.join(unknown_fields)}")
                return self.form_invalid(form)
            
            user.student_card_data = clean_dict
            print("Student card data saved to user")

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