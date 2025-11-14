"""
URL configuration for sarvsaathi_api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/accounts/', include('apps.accounts.urls')),
    # --- ADD THESE NEW LINES ---
    
    # 1. This is the "Front Desk" / Login Endpoint
    # A user will POST their {email, password} to this URL
    # and get back their Access Token.
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    
    # This tells Django to send any URL starting with 'api/appointments/'
    # to the new 'urls.py' file we just created in that app.
    path('api/appointments/', include('apps.appointments.urls')),
    
    # 2. This is the "Token Refresh" Endpoint
    # (For later, to get a new token when the old one expires)
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
