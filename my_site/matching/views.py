from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated

from django.shortcuts import render
from django.http import JsonResponse

from .models import MatchingQueue
from matching_mixins.mixins import MatchingMixin

def start_matching_page(request):
    return render(request, 'matching/start_matching.html')

def do_matching(request, location):
    return render(request, 'matching/do_matching.html',{'location':location})

class StartMatching(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        return Response({"message": "match_start"}, status=status.HTTP_200_OK)
    
class MealWatitingStatusView(MatchingMixin, APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        response_data = self.get_meal_waiting_status(request.data)
        return Response(response_data, status=status.HTTP_200_OK)