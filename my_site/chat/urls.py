from django.urls import path
from . import views

urlpatterns = [
    path("",views.index, name='index'),
    path("roomNum/<str:room_id>/",views.room, name='room'),
]
