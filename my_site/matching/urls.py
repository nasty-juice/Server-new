from django.urls import path, include
from .views import start_matching_page, cancel_matching, do_matching

urlpatterns = [
    path('',start_matching_page,name='start_matching_page'),
    path('cancel_matching',cancel_matching, name='cancel_matching'),
    path('group/<int:group_id>/', include('chat.urls'), name='group_page'),
    path('matching/<str:location>',do_matching, name = 'do_matching'),
]
