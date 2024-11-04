from django.urls import path
from .views import start_matching, start_matching_page, cancel_matching,group_page,quit_group

urlpatterns = [
    path('',start_matching_page,name='start_matching_page'),
    path('matching/', start_matching, name='start_matching'),
    path('cancel_matching',cancel_matching, name='cancel_matching'),
    path('group/<int:group_id>/', group_page, name='group_page'),
    path('quit_group/<int:group_id>',quit_group, name="quit_group"),
]
