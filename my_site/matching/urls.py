from django.urls import path, include
from . import views

urlpatterns = [
    path('',views.start_matching_page,name='start_matching_page'),
    path('matching/<str:location>',views.do_matching, name = 'do_matching'),
    path('api/group/<int:group_id>/', include('chat.urls'), name='group_page'),
    path('api/matching/',views.StartMatching.as_view(), name = 'start_matching'),
    path('api/waiting-status/', views.MealWatitingStatusView.as_view(), name='waiting_status'),
]
