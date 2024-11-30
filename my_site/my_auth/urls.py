from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token

app_name = 'my_auth'

router = DefaultRouter()
router.register('signup', views.CustomSignupViewSet)


urlpatterns = [
    path('accounts/', include('allauth.urls')),
    
    path('api/', include(router.urls)), # 회원가입 엔드포인트 /my_auth/api/signup/ 을 위한 라우터
    path('api/token-login/', views.CustomLoginView.as_view(), name='token_login'), # Token Authentication 을 위한 로그인 엔드포인트 /my_auth/api-token-auth/
    path('api/user/me/', views.UserDetailView.as_view(), name='user_detail'),   # 로그인한 사용자의 정보를 가져오는 엔드포인트 /my_auth/user/me/
    path('api/user/me/logout/', views.UserLogoutView.as_view(), name='user_logout'), # 로그아웃 엔드포인트 /my_auth/user/me/logout/
    path('api/user/me/password-change/', views.UserPasswordChangeView.as_view(), name='user_password_change'), # 비밀번호 변경 엔드포인트 /my_auth/user/me/password-change/
    path('api/user/me/delete/', views.UserDeleteView.as_view(), name='user_delete'), # 회원탈퇴 엔드포인트 /my_auth/user/me/delete/

    path('api/check-chat-room/', views.CheckChatRoom.as_view(), name='check_join_room'), # 사용자의 join_room 필드를 확인하는 엔드포인트 /my_auth/api/check-join-room/
    path('api/can-match/', views.CanMatch.as_view(), name='can_match'), # 사용자의 join_room 필드를 확인하는 엔드포인트 /my_auth/api/check-join-room/

    path('temp/', views.temp_view, name='temp_view'),
    path('temp/class/', views.TempClassView.as_view(), name='temp_class_view'),
    
    path('landing-page/', views.langing_page, name='landing_page'),
    path('signup-success/', views.signup_success_view, name='signup_success_view'),
]