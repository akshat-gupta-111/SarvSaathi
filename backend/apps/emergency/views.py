from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
import urllib.parse
import logging
from .notifications import send_emergency_sms, send_emergency_email, send_emergency_whatsapp
from apps.accounts.models import DoctorProfile, Patient
from apps.appointments.models import TimeSlot, Appointment
from .models import EmergencyRequest
from .serializers import (
    TriageInputSerializer, TriageOutputSerializer, 
    RequestDoctorInputSerializer, RequestDoctorOutputSerializer,
    SpecialistResultSerializer
)
from .utils import haversine, TRIAGE_TO_SPECIALTY

from .notifications import send_emergency_sms, send_emergency_whatsapp

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
        
        # 1. Find the user's "self" patient profile
        try:
            patient = request.user.patients.get(relationship='self')
        except Patient.DoesNotExist:
            return Response(
                {"error": "No 'self' patient profile found. Please complete your profile."}, 
                status=status.HTTP_400_BAD_REQUEST
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
            specialty__iexact=specialty,
            latitude__isnull=False,
            longitude__isnull=False
        )

        # 5. Calculate distance for each doctor
        user_coords = (data['user_lat'], data['user_lng'])
        doctor_list = []
        for doc in doctors:
            doc_coords = (doc.latitude, doc.longitude)
            distance = haversine(user_coords[0], user_coords[1], doc_coords[0], doc_coords[1])
            doc.distance_km = round(distance, 2) # Add distance as a temporary attribute
            doctor_list.append(doc)
            
        # 6. Sort by distance
        doctor_list.sort(key=lambda x: x.distance_km)
        
        # 7. Get the top 3
        top_doctors = doctor_list[:3]

        # 8. --- THIS IS THE FIX ---
        # We now pass the raw `top_doctors` *objects* to the output_data.
        # The TriageOutputSerializer will handle serializing them.
        output_data = {
            "log_id": log_entry.id,
            "doctors": top_doctors # <-- No more .data here!
        }
        # --- END FIX ---
        
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
            log_entry = EmergencyRequest.objects.get(id=log_id, patient__account_holder=request.user)
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
            start_time=now,
            end_time=now + timedelta(minutes=30),
            mode='IN_CLINIC',
            is_available=False
        )
        special_appointment = Appointment.objects.create(
            patient=log_entry.patient,
            time_slot=special_slot,
            status='CONFIRMED',
            payment_status='UNPAID',
            patient_notes=f"EMERGENCY: {log_entry.triage_category}\n--\n{log_entry.patient_notes}",
            amount_paid=0.00
        )

        # 4. Update the log
        log_entry.status = 'ACCEPTED'
        log_entry.doctor = doctor
        log_entry.linked_appointment = special_appointment
        log_entry.save()

        # 5. --- Send Notifications to Doctor (FIXED) ---
        patient = log_entry.patient
        patient_name = f"{patient.first_name} {patient.last_name}"
        message_body = (
            f"EMERGENCY ALERT: {patient_name} is en route to your clinic.\n"
            f"Triage: {log_entry.triage_category}\n"
            f"Notes: {log_entry.patient_notes}\n"
            f"Patient Phone: {patient.phone_number}"
        )
        
        # We wrap notifications in a try/except block.
        try:
            logging.info("Attempting to send emergency notifications...")
            
            # Call 1: Send SMS (using Twilio)
            send_emergency_sms(doctor.phone_number, message_body)
            
            # Call 2: Send Email (using Gmail)
            send_emergency_email(doctor.user.email, message_body)

            # Call 3: Send WhatsApp (using Twilio)
            send_emergency_whatsapp(doctor.phone_number, message_body)

            logging.info("Notification dispatch complete.")
        except Exception as e:
            logging.error(f"CRITICAL: Notification dispatch failed for Appointment {special_appointment.id}: {e}")

        # 6. --- Prepare Response for Patient ---
        destination = f"{doctor.latitude},{doctor.longitude}"
        params = {"api": "1", "destination": destination}
        # Fixed the markdown link bug from the previous file
        directions_link = "[https://www.google.com/maps/dir/](https://www.google.com/maps/dir/)?" + urllib.parse.urlencode(params)

        output_data = {
            "appointment_id": special_appointment.id,
            "doctor_name": f"Dr. {doctor.first_name} {doctor.last_name}",
            "clinic_address": doctor.clinic_address,
            "get_directions_link": directions_link
        }

        return Response(RequestDoctorOutputSerializer(output_data).data, status=status.HTTP_201_CREATED)

