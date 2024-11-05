from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter

app_name = 'my_auth'

router = DefaultRouter()
router.register('signup', views.CustomSignupViewSet)


urlpatterns = [
    path('accounts/', include('allauth.urls')),
    # path('signup/', views.CustomSignupView.as_view(), name='account_signup'),
    path('api/accounts/signup/', views.APICustomSignupView.as_view(), name='account_signup'),
    
    path('', include(router.urls)),
    
    path('temp/', views.temp_view, name='temp_view'),
    path('temp/class/', views.TempClassView.as_view(), name='temp_class_view'),
    
    path('landing-page/', views.langing_page, name='landing_page'),
    path('signup-success/', views.signup_success_view, name='signup_success_view'),
]