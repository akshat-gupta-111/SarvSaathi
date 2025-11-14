from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from .models import TimeSlot
from .serializers import TimeSlotSerializer, TimeSlotListSerializer
from .permissions import IsDoctor # Import our new permission

# --- View 1: For Doctors (CREATE and LIST their own slots) ---

class DoctorTimeSlotListCreateView(generics.ListCreateAPIView):
    """
    API View for authenticated DOCTORS to:
    - GET: List all of their own time slots.
    - POST: Create a new time slot for themselves.
    """
    # Use the writable serializer
    serializer_class = TimeSlotSerializer
    
    # Use our custom permission to lock this view to doctors only
    permission_classes = [IsAuthenticated, IsDoctor]

    def get_queryset(self):
        """
        This view should only return time slots for the
        currently logged-in doctor.
        """
        # self.request.user is the logged-in CustomUser
        # .doctor_profile is the linked DoctorProfile
        return TimeSlot.objects.filter(doctor=self.request.user.doctor_profile)

    def perform_create(self, serializer):
        """
        When a doctor creates a new slot, automatically assign
        it to their own DoctorProfile.
        """
        # The 'doctor' field in the serializer is read-only,
        # so we set it here using the logged-in user.
        serializer.save(doctor=self.request.user.doctor_profile)

# --- View 2: For Patients (LIST available slots for a doctor) ---

class PatientTimeSlotListView(generics.ListAPIView):
    """
    API View for ANY user (Patient or public) to:
    - GET: List all *available* and *future* time slots for a
      specific doctor.
    """
    # Use the read-only serializer with nested doctor info
    serializer_class = TimeSlotListSerializer
    
    # This view is public for browsing
    permission_classes = [AllowAny]

    def get_queryset(self):
        """
        This view returns slots based on the doctor_id in the URL.
        """
        # 1. Get the doctor's ID from the URL (e.g., /doctors/2/time-slots/)
        # We will name this 'doctor_id' in our urls.py file
        doctor_id = self.kwargs.get('doctor_id')
        if not doctor_id:
            return TimeSlot.objects.none() # Return nothing if no ID

        # 2. Filter by:
        #    - The specific doctor
        #    - Slots that are still available
        #    - Slots that are in the future (not in the past)
        return TimeSlot.objects.filter(
            doctor__id=doctor_id,
            is_available=True,
            start_time__gte=timezone.now() # Only show future slots
        )