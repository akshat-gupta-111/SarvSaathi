from django.shortcuts import render

# Create your views here.
# backend/apps/accounts/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny # <-- Import this!

# We're overriding our 'IsAuthenticated' default for this one test view
class HealthCheckView(APIView):
    permission_classes = [AllowAny] # Anyone can see this page

    def get(self, request, *args, **kwargs):
        # The Response object is DRF's special sauce.
        # It automatically converts this Python dictionary to JSON.
        return Response({"message": "SarvSaathi API is live and healthy!"})