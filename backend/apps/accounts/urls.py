# backend/apps/accounts/urls.py

from django.urls import path
from .views import HealthCheckView # <-- Import our new view

urlpatterns = [
    # When a user visits /api/accounts/health-check/
    # show them the HealthCheckView.
    path('health-check/', HealthCheckView.as_view(), name='health-check'),
]