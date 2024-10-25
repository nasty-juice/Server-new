from django.urls import path, include
from . import views

app_name = 'my_auth'

urlpatterns = [
    path('', views.initial_auth_view, name='initial_auth_view'),
    path('accounts/', include('allauth.urls')),
    path('student-card-auth/', views.StudentCardAuthView.as_view(), name='student_card_auth'),
    
]