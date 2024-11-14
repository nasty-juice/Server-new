from django.urls import path
from .views import TaxiWaitingStatusView, TaxiMatchingLocationCheckView

app_name = 'taxi_matching'

urlpatterns = [
    path('api/waiting-status/', TaxiWaitingStatusView.as_view(), name='waiting_status'),
    path('api/location-check/', TaxiMatchingLocationCheckView.as_view(), name='location_check'),
]
