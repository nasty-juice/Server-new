from django.urls import path,include
from . import views

my_app = 'my_app'

urlpatterns = [
    path('', views.initial_view, name='initial_view'),
    # path('login/', views.redirect_to_auth_login, name='redirect_to_auth_login'),
    # path('signup/', views.redirect_to_auth_signup, name='redirect_to_auth_signup'),
    
]