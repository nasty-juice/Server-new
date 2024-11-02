from django.urls import path,include
from . import views

my_app = 'my_app'

urlpatterns = [
    path('', views.home_view, name='home_view'),
    path('home/', views.home_view, name='home_view'),
    path('private-media/<path:file_path>', views.private_media_view, name='private_media_view'),
]