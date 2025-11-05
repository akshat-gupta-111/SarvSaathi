# backend/apps/accounts/views.py
# We need IsAuthenticated to "lock" our doors
from rest_framework.permissions import AllowAny, IsAuthenticated 
from rest_framework import generics
from .models import CustomUser, Patient, DoctorProfile # Import new models
from .serializers import (
    UserRegistrationSerializer,
    PatientSerializer,       # Import new serializer
    DoctorProfileSerializer  # Import new serializer
)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics
from .models import CustomUser
from .serializers import UserRegistrationSerializer # Import our new serializer

# You already have this "Health Check" view
class HealthCheckView(APIView):
    permission_classes = [AllowAny] 
    def get(self, request, *args, **kwargs):
        return Response({"message": "SarvSaathi API is live and healthy!"})

# --- ADD THIS NEW VIEW ---
class RegisterView(generics.CreateAPIView):
    """
    This is the /register endpoint.
    It's a "Create-Only" view, so it only accepts POST requests.
    """
    queryset = CustomUser.objects.all()
    
    # This is critical. It makes the view PUBLIC.
    # We are overriding our default (IsAuthenticated)
    # so that new users can actually sign up.
    permission_classes = (AllowAny,)
    
    # Tell this view to use the serializer we just made
    serializer_class = UserRegistrationSerializer

# backend/apps/accounts/views.py

# --- UPDATE YOUR IMPORTS ---


# ... (HealthCheckView and RegisterView are already here) ...


# --- ADD THESE NEW VIEWS ---

# --- FOR PATIENTS ---
class PatientListView(generics.ListCreateAPIView):
    """
    This is the "locked door" for a patient's family list.
    - GET: Lists all patients belonging to the logged-in user.
    - POST: Creates a new patient (e.g., "Child") for the logged-in user.
    """
    # This is the "lock". Only authenticated users can access this.
    permission_classes = [IsAuthenticated]
    serializer_class = PatientSerializer
    
    def get_queryset(self):
        # This is the "key". It filters the list to show *only*
        # the Patient records that belong to the logged-in user.
        return Patient.objects.filter(account_holder=self.request.user)
        
    def perform_create(self, serializer):
        # When creating a new patient, automatically set the
        # account_holder to the currently logged-in user.
        serializer.save(account_holder=self.request.user)

class PatientDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    This is the "locked door" for a *single* patient record.
    - GET /patients/1/: Gets the details for patient #1
    - PUT /patients/1/: Updates patient #1 (This is "Complete Profile")
    - DELETE /patients/1/: Deletes patient #1
    """
    permission_classes = [IsAuthenticated]
    serializer_class = PatientSerializer
    
    def get_queryset(self):
        # A user can ONLY see/edit/delete *their own* patient records.
        # This is a critical security feature.
        return Patient.objects.filter(account_holder=self.request.user)

# --- FOR DOCTORS ---
class DoctorProfileView(generics.RetrieveUpdateAPIView):
    """
    This is the "locked door" for a doctor's own profile.
    - GET: Gets the logged-in doctor's profile
    - PUT: Updates the logged-in doctor's profile
    """
    permission_classes = [IsAuthenticated]
    serializer_class = DoctorProfileSerializer
    
    def get_object(self):
        # This is the "key". It finds the *one* profile
        # linked to the logged-in doctor.
        return self.request.user.doctor_profile