from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token

app_name = 'my_auth'

router = DefaultRouter()
router.register('signup', views.CustomSignupViewSet)


urlpatterns = [
    path('accounts/', include('allauth.urls')),
    
    path('', include(router.urls)), # 회원가입 엔드포인트 /signup/ 을 위한 라우터
    path('user/me/', views.UserDetailView.as_view(), name='user_detail'),   # 로그인한 사용자의 정보를 가져오는 엔드포인트 /my_auth/user/me/
    path('token-login/', views.CustomLoginView.as_view(), name='token_login'), # Token Authentication 을 위한 로그인 엔드포인트 /my_auth/api-token-auth/

    path('temp/', views.temp_view, name='temp_view'),
    path('temp/class/', views.TempClassView.as_view(), name='temp_class_view'),
    
    path('landing-page/', views.langing_page, name='landing_page'),
    path('signup-success/', views.signup_success_view, name='signup_success_view'),
]