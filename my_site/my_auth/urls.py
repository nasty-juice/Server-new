from django.urls import path, include
from . import views
from django.contrib.auth.views import LoginView

app_name = 'my_auth'

urlpatterns = [
    path('', views.initial_auth_view, name='initial_auth_view'),
    path('accounts/', include('allauth.urls')),
    
]