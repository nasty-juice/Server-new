from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.views import APIView

from matching.models import MatchingQueue

# Create your views here.
@api_view(['POST'])
def start_taxi_matching(request):
    
    return render(request, 'taxi_matching/start_matching.html')

@api_view(['GET'])
def waitingStatusView(APIView):
    try:
        pass
    except:
        pass