from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView, View, FormView
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile

from allauth.account.views import SignupView
from allauth.account.utils import send_email_confirmation

from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework import viewsets

from my_app.models import CustomUser
from .serializers import CustomSignupSerializer
from .forms import CustomSignupForm
from .utils import perform_ocr, get_unknown_fields

class UserPasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")
        
        if not user.check_password(old_password):
            return Response({"error": "Invalid password"}, status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(new_password)
        user.save()
        
        return Response({"message": "Password changed successfully"}, status=status.HTTP_200_OK)

# 내 정보 가져오기
class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]      # 로그인한 사용자만 접근 가능
    
    def get(self, request):
        user = request.user
        serializer = CustomSignupSerializer(user)
        response_data = {
            # "id" : serializer.data["id"], # 서버에서 pk id 전송 필요 없음.
            "username" : serializer.data["username"],
            "email" : serializer.data["email"],
            "student_number" : serializer.data["student_number"],
            "student_name" : serializer.data["student_name"],
        }
        return Response(response_data, status=status.HTTP_200_OK)

# 로그인
class CustomLoginView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        print(email, password)
        # 이메일로 사용자를 인증
        try:
            user = CustomUser.objects.get(email=email)
            
            # 이메일 인증 여부 확인
            if not user.email_verified:
                return Response({"error": "Email not verified"}, status=status.HTTP_403_FORBIDDEN)
            
            # 비밀번호를 직접 검증
            if user.check_password(password):  # 비밀번호가 맞으면 True 반환
                token, created = Token.objects.get_or_create(user=user)
                return Response({"token": token.key}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)

        except CustomUser.DoesNotExist:
            return Response({"error": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)

# 회원가입
class CustomSignupViewSet(viewsets.ModelViewSet):
    serializer_class = CustomSignupSerializer
    queryset = CustomUser.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # 이메일 인증 링크 전송
        send_email_confirmation(request, user)
        
        response_data = {
            "email" : serializer.data["email"],
            "student_number" : serializer.data["student_number"],
            "student_name" : serializer.data["student_name"],
        }
        
        headers = self.get_success_headers(serializer.data)
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)
    
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




