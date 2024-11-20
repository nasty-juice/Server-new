from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.shortcuts import render

from matching_mixins.mixins import MatchingMixin

from .utils import check_user_location

@api_view(['POST'])
def start_taxi_matching(request):
    return render(request, 'taxi_matching/start_matching.html')

class TaxiWaitingStatusView(MatchingMixin, APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        response_data = self.get_taxi_waiting_status(request.data)
        return Response(response_data, status=status.HTTP_200_OK)

class TaxiMatchingLocationCheckView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        starting_point = request.data.get("starting_point")
        user_lat = request.data.get("latitude")
        user_lon = request.data.get("longitude")
        
        if user_lat is None or user_lon is None:
            return Response({"message": "Invalid request"}, status=status.HTTP_400_BAD_REQUEST)
        
        if check_user_location(starting_point, user_lat, user_lon):
            return Response({"message": "Valid location."}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Invalid loaction."}, status=status.HTTP_400_BAD_REQUEST)
        
