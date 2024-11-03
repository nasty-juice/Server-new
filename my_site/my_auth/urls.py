from django.urls import path, include
from . import views

app_name = 'my_auth'

urlpatterns = [
    path('accounts/', include('allauth.urls')),
    path('signup/', views.CustomSignupView.as_view(), name='account_signup'),
    path("verify-email/", views.EmailVerificationView.as_view(), name="verify_email"),
    path('landing-page/', views.langing_page, name='landing_page'),
    path('signup-success/', views.signup_success_view, name='signup_success_view'),
    # path('student-card-auth/', views.StudentCardAuthView.as_view(), name='student_card_auth'),
]