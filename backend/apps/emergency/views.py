from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from datetime import timedelta
import urllib.parse
import logging
from .notifications import send_emergency_sms, send_emergency_email, send_emergency_whatsapp
from apps.accounts.models import DoctorProfile, FamilyMember, EmergencyContact
from apps.appointments.models import TimeSlot, Appointment
from .models import EmergencyRequest
from .serializers import (
    TriageInputSerializer, TriageOutputSerializer, 
    RequestDoctorInputSerializer, RequestDoctorOutputSerializer,
    SpecialistResultSerializer
)
from .utils import haversine, TRIAGE_TO_SPECIALTY

logger = logging.getLogger(__name__)

# --- View 1: Step 1 (Patient) -> Find Specialists ---

class FindSpecialistView(generics.GenericAPIView):
    """
    API View for Step 1 of the emergency flow.
    Takes a patient's location and triage, creates a log,
    and returns a list of the closest, most relevant doctors.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TriageInputSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        # 1. Find the user's "self" family member profile
        try:
            patient = request.user.family_members.get(relationship='self')
        except FamilyMember.DoesNotExist:
            # Auto-create if missing
            patient = FamilyMember.objects.create(
                user=request.user,
                relationship='self',
                first_name=request.user.first_name or 'Self',
                last_name=request.user.last_name or ''
            )

        # 2. Create the EmergencyRequest log
        log_entry = EmergencyRequest.objects.create(
            patient=patient,
            triage_category=data['triage_category'],
            patient_notes=data.get('patient_notes', ''),
            user_lat=data['user_lat'],
            user_lng=data['user_lng'],
            status='SEARCHING'
        )

        # 3. Find the required specialty
        specialty = TRIAGE_TO_SPECIALTY.get(data['triage_category'], 'General Physician')
        
        # 4. Find all verified doctors with that specialty and location
        doctors = DoctorProfile.objects.filter(
            is_verified=True, 
            specialty__icontains=specialty,
            clinic_latitude__isnull=False,
            clinic_longitude__isnull=False
        )

        # 5. Calculate distance for each doctor
        user_coords = (data['user_lat'], data['user_lng'])
        doctor_list = []
        for doc in doctors:
            doc_coords = (float(doc.clinic_latitude), float(doc.clinic_longitude))
            distance = haversine(user_coords[0], user_coords[1], doc_coords[0], doc_coords[1])
            doc.distance_km = round(distance, 2)
            doctor_list.append(doc)
            
        # 6. Sort by distance
        doctor_list.sort(key=lambda x: x.distance_km)
        
        # 7. Get the top 3
        top_doctors = doctor_list[:3]

        # 8. Return serialized data
        output_data = {
            "log_id": log_entry.id,
            "doctors": top_doctors
        }
        
        return Response(TriageOutputSerializer(output_data).data, status=status.HTTP_200_OK)




# --- View 2: Step 2 (Patient) -> Request a Specialist ---

class RequestDoctorView(generics.GenericAPIView):
    """
    API View for Step 2 of the emergency flow.
    Patient has chosen a doctor. This view creates the "Special Appointment",
    bypasses payment, and sends notifications.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = RequestDoctorInputSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        log_id = data['log_id']
        doctor_id = data['doctor_id']

        # 1. Get the log and doctor
        try:
            log_entry = EmergencyRequest.objects.get(id=log_id, patient__user=request.user)
            doctor = DoctorProfile.objects.get(id=doctor_id, is_verified=True)
        except (EmergencyRequest.DoesNotExist, DoctorProfile.DoesNotExist):
            return Response({"error": "Invalid request or doctor ID."}, status=status.HTTP_404_NOT_FOUND)

        # 2. Check if this request is already handled
        if log_entry.status != 'SEARCHING':
            return Response({"error": "This request is no longer active."}, status=status.HTTP_400_BAD_REQUEST)

        # 3. --- Create the "Special Appointment" ---
        now = timezone.now()
        special_slot = TimeSlot.objects.create(
            doctor=doctor,
            date=now.date(),
            start_time=now.time(),
            end_time=(now + timedelta(minutes=30)).time(),
            mode='in_clinic',
            status='booked'
        )
        special_appointment = Appointment.objects.create(
            user=request.user,
            family_member=log_entry.patient,
            doctor=doctor,
            time_slot=special_slot,
            status='confirmed',
            payment_status='unpaid',
            symptoms=f"EMERGENCY: {log_entry.triage_category}",
            notes_for_doctor=log_entry.patient_notes,
            consultation_fee=0.00,
            amount_paid=0.00
        )

        # 4. Update the log
        log_entry.status = 'ACCEPTED'
        log_entry.doctor = doctor
        log_entry.linked_appointment = special_appointment
        log_entry.save()

        # 5. --- Send Notifications to Doctor ---
        patient = log_entry.patient
        patient_name = f"{patient.first_name} {patient.last_name}"
        message_body = (
            f"EMERGENCY ALERT: {patient_name} is en route to your clinic.\n"
            f"Triage: {log_entry.triage_category}\n"
            f"Notes: {log_entry.patient_notes}\n"
            f"Patient Phone: {patient.phone_number or request.user.phone_number}"
        )
        
        try:
            logger.info("Attempting to send emergency notifications...")
            
            if doctor.clinic_phone:
                send_emergency_sms(doctor.clinic_phone, message_body)
            
            if doctor.user.email:
                send_emergency_email(doctor.user.email, message_body)

            if doctor.clinic_phone:
                send_emergency_whatsapp(doctor.clinic_phone, message_body)

            logger.info("Notification dispatch complete.")
        except Exception as e:
            logger.error(f"Notification dispatch failed: {e}")

        # 6. --- Prepare Response for Patient ---
        if doctor.clinic_latitude and doctor.clinic_longitude:
            destination = f"{doctor.clinic_latitude},{doctor.clinic_longitude}"
            params = {"api": "1", "destination": destination}
            directions_link = "https://www.google.com/maps/dir/?" + urllib.parse.urlencode(params)
        else:
            directions_link = ""

        output_data = {
            "appointment_id": special_appointment.id,
            "doctor_name": f"Dr. {doctor.user.first_name} {doctor.user.last_name}",
            "clinic_address": doctor.clinic_address,
            "get_directions_link": directions_link
        }

        return Response(RequestDoctorOutputSerializer(output_data).data, status=status.HTTP_201_CREATED)


# --- View 3: Trigger SOS Alert ---

class TriggerSOSView(APIView):
    """
    Trigger an SOS alert - sends emergency notifications to all contacts.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        lat = request.data.get('latitude')
        lng = request.data.get('longitude')
        message = request.data.get('message', 'Emergency! Need help!')

        # Get user's emergency contacts
        contacts = EmergencyContact.objects.filter(user=user)
        
        if not contacts.exists():
            return Response({
                "warning": "No emergency contacts configured. Please add emergency contacts in your profile.",
                "contacts_notified": 0
            }, status=status.HTTP_200_OK)

        # Build emergency message
        location_link = ""
        if lat and lng:
            location_link = f"https://www.google.com/maps?q={lat},{lng}"
        
        user_name = user.get_full_name() or user.email
        emergency_message = (
            f"🚨 EMERGENCY SOS from {user_name}!\n\n"
            f"Message: {message}\n"
        )
        if location_link:
            emergency_message += f"Location: {location_link}\n"
        emergency_message += f"Contact: {user.phone_number or user.email}"

        # Send to all contacts
        notified_count = 0
        for contact in contacts:
            try:
                if contact.phone_number:
                    send_emergency_sms(contact.phone_number, emergency_message)
                    notified_count += 1
                if contact.email:
                    send_emergency_email(contact.email, emergency_message)
            except Exception as e:
                logger.error(f"Failed to notify {contact.name}: {e}")

        return Response({
            "message": "SOS alert sent successfully",
            "contacts_notified": notified_count
        }, status=status.HTTP_200_OK)


# --- View 4: Get Nearby Hospitals (Mock) ---

class NearbyHospitalsView(APIView):
    """
    Get nearby hospitals based on location.
    This is a mock implementation - integrate with Google Places API for production.
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')

        if not lat or not lng:
            return Response({
                "error": "Latitude and longitude are required"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Mock hospital data
        hospitals = [
            {
                "name": "City General Hospital",
                "address": "123 Main Street, New Delhi",
                "phone": "+91-11-12345678",
                "distance": "2.3 km",
                "emergency": True,
                "rating": 4.5
            },
            {
                "name": "Apollo Hospital",
                "address": "456 Health Avenue, New Delhi",
                "phone": "+91-11-87654321",
                "distance": "3.8 km",
                "emergency": True,
                "rating": 4.8
            },
            {
                "name": "Max Super Specialty Hospital",
                "address": "789 Care Road, New Delhi",
                "phone": "+91-11-11223344",
                "distance": "5.1 km",
                "emergency": True,
                "rating": 4.6
            }
        ]

        return Response({
            "hospitals": hospitals,
            "total": len(hospitals)
        }, status=status.HTTP_200_OK)

