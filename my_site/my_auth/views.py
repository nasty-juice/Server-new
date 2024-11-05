from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView, View, FormView
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile

from allauth.account.views import SignupView
from allauth.account.utils import send_email_confirmation

from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework import viewsets

from my_app.models import CustomUser
from .forms import CustomSignupForm
from .serializers import CustomSignupSerializer
from .utils import perform_ocr, get_unknown_fields


class CustomSignupViewSet(viewsets.ModelViewSet):
    serializer_class = CustomSignupSerializer
    queryset = CustomUser.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # 이메일 인증 링크 전송
        send_email_confirmation(request, user)
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        
        
        
# Create your views here.
@login_required
def signup_success_view(request):
    return render(request, 'my_auth/signup_success_view.html')

def langing_page(request):
    return render(request, 'my_auth/landing_page.html')

@csrf_exempt
@api_view(['POST'])
def temp_view(request):
    
    print(request.data)
    return Response({"message": "Hello, World!"}, status=status.HTTP_200_OK)

@method_decorator(csrf_exempt, name='dispatch')
class TempClassView(APIView):
    def post(self, request):
        print(request.data)
        return Response({"message": "Hello, World!"}, status=status.HTTP_200_OK)

@method_decorator(csrf_exempt, name='dispatch')
class APICustomSignupView(APIView):
    permission_classes = [AllowAny]

    model = CustomUser
    form_class = CustomSignupForm

    def post(self, request):
        print("request.data: ", request.data)
        print("request.post: ", request.POST)
        print("request.files: ", request.FILES)

        # form = CustomSignupForm(request.data)
        
        return Response({"message": "Hello, World!"}, status=status.HTTP_200_OK)
    
        if form.is_valid():
            # user = form.save(request)
            print(form.cleaned_data)
            return Response({"message": "User created successfully."}, status=status.HTTP_201_CREATED)
        else:
            return Response({"error": form.errors}, status=status.HTTP_400_BAD_REQUEST)

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




