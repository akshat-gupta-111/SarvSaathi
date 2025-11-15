from rest_framework import serializers
from django.utils import timezone
from django.conf import settings
import requests
from apps.accounts.models import Patient
from .models import TimeSlot, Appointment, DoctorProfile 
import urllib.parse
from apps.accounts.models import DoctorProfile
import logging 
import random 


# Make sure to import all the models we'll need
from .models import TimeSlot, Appointment
from apps.accounts.models import DoctorProfile

# --- Serializer 1: A small, read-only serializer for doctor info ---
class NestedDoctorSerializer(serializers.ModelSerializer):
    """
    A simple, read-only serializer to show basic doctor info.
    We'll "nest" this inside the TimeSlotListSerializer.
    """
    full_name = serializers.SerializerMethodField()
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = DoctorProfile
        fields = ('id', 'full_name', 'email', 'specialty')

    def get_full_name(self, obj):
        # Combines first and last name for a clean display
        return f"Dr. {obj.first_name} {obj.last_name}"

# --- Serializer 2: For PATIENT to READ available time slots ---
class TimeSlotListSerializer(serializers.ModelSerializer):
    """
    A READ-ONLY serializer for PATIENTS to browse available slots.
    It includes the nested doctor information.
    """
    # This nests the NestedDoctorSerializer inside this one
    doctor = NestedDoctorSerializer(read_only=True)

    class Meta:
        model = TimeSlot
        fields = ('id', 'doctor', 'start_time', 'end_time', 'mode', 'is_available')

# --- Serializer 3: For DOCTOR to CREATE their time slots ---


class TimeSlotCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for a Doctor to CREATE a new TimeSlot.
    This is a ModelSerializer, so it has a .save() method.
    """
    class Meta:
        model = TimeSlot
        fields = ['id', 'start_time', 'end_time', 'mode', 'doctor']
        
        # The 'doctor' field is set automatically in the view, not by the user.
        # The 'id' is read-only because it's set by the database.
        read_only_fields = ['id', 'doctor']

    def validate(self, data):
        """
        Check that the start_time is before the end_time and not in the past.
        """
        if data['start_time'] >= data['end_time']:
            raise serializers.ValidationError("End time must be after start time.")
        
        if data['start_time'] <= timezone.now():
            raise serializers.ValidationError("Cannot create time slots in the past.")
        return data


# --- Serializer 4 (Phase 2): For Patient to START a booking ---

class AppointmentCreateSerializer(serializers.Serializer):
    """
    Serializer to CREATE an appointment.
    Takes a time_slot_id and a patient_id.
    """
    time_slot_id = serializers.IntegerField(write_only=True)
    patient_id = serializers.IntegerField(write_only=True)

    def validate(self, data):
        """
        Validate the time_slot_id and patient_id.
        This is where we check all our rules.
        """
        request = self.context['request']
        
        # --- 1. Validate Time Slot ---
        try:
            time_slot = TimeSlot.objects.get(
                id=data['time_slot_id'],
                is_available=True,
                start_time__gte=timezone.now()
            )
        except TimeSlot.DoesNotExist:
            raise serializers.ValidationError("This time slot is not available.")

        # --- 2. THE FIX: Check if slot is already linked ---
        # A OneToOneField's reverse relation ('appointment') will raise
        # DoesNotExist if no appointment is linked. This is what we want.
        try:
            _ = time_slot.appointment # Check if the reverse 'appointment' exists
            
            # If the line above *succeeds*, it means a link exists.
            # This is bad.
            raise serializers.ValidationError("This time slot is already pending or booked.")
        
        except Appointment.DoesNotExist:
            # This is the SUCCESS case. No appointment is linked.
            pass 
        # --- END FIX ---

        # --- 3. Validate Patient ---
        try:
            patient = Patient.objects.get(
                id=data['patient_id'],
                account_holder=request.user
            )
        except Patient.DoesNotExist:
            raise serializers.ValidationError("Invalid patient ID.")

        # --- 4. Validate Profile Complete (YOUR RULE) ---
        if not patient.is_complete:
            raise serializers.ValidationError(
                "Please complete this patient's profile before booking."
            )

        # --- Success! ---
        self.context['time_slot'] = time_slot
        self.context['patient'] = patient
        return data

# --- Serializer 5 (Phase 2): For Patient to GET the "approval_url" ---

class AppointmentInitiateSerializer(serializers.Serializer):
    """
    A READ-ONLY serializer to send the PayPal 'approval_url'
    back to the patient's frontend.
    """
    approval_url = serializers.URLField()

# --- Serializer 6 (Phase 2): For Frontend to EXECUTE the payment ---

class AppointmentExecuteSerializer(serializers.Serializer):
    """
    The serializer the frontend uses to send the 'paymentId'
    and 'PayerID' back to our server after the user approves
    the payment on the PayPal website.
    """
    paymentId = serializers.CharField(max_length=100)
    PayerID = serializers.CharField(max_length=100)

# --- Serializer 7 (Phase 3+): For Patient to VIEW their confirmed bookings ---
# We will use this in the next phase, but it's good to define it now.
class AppointmentDetailSerializer(serializers.ModelSerializer):
    """
    A full, read-only serializer to show all the details
    of a confirmed appointment. (Used for "My Appointments" page).
    """
    time_slot = TimeSlotListSerializer(read_only=True)
    
    class Meta:
        model = Appointment
        fields = (
            'id',
            'patient',
            'time_slot',
            'status',
            'payment_status',
            'payment_order_id', 
            'created_at',
        )
        read_only_fields = fields


class PatientAppointmentDoctorSerializer(serializers.ModelSerializer):
    """
    A nested serializer to show *only* the doctor's public info.
    """
    # --- THIS IS THE FIX ---
    # 1. We change from CharField to SerializerMethodField
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = DoctorProfile
        # 2. We add 'full_name' to the fields list
        fields = ['full_name', 'specialty']

    # 3. We add the "get" method for our new field
    def get_full_name(self, obj):
        """
        Combines the doctor's first and last name.
        'obj' is the DoctorProfile instance.
        """
        # We can even add the "Dr." prefix here.
        return f"Dr. {obj.first_name} {obj.last_name}"


class PatientAppointmentTimeSlotSerializer(serializers.ModelSerializer):
    """
    A nested serializer to show the time slot and doctor info.
    """
    # Use the serializer above to show the doctor's details
    doctor = PatientAppointmentDoctorSerializer(read_only=True)
    
    class Meta:
        model = TimeSlot
        fields = ['start_time', 'end_time', 'mode', 'doctor']

class PatientAppointmentListSerializer(serializers.ModelSerializer):
    """
    Main serializer for the "My Appointments" list.
    This serializer combines all the data a patient needs.
    """
    # Use the serializer above to show the nested time slot
    time_slot = PatientAppointmentTimeSlotSerializer(read_only=True)
    
    # This is the NEW field that uses your Google Maps logic
    get_directions_link = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = [
            'id',
            'status',
            'time_slot',
            'get_directions_link',
            'patient_notes',
            'video_call_link',
        ]
        
    def get_get_directions_link(self, obj):
        """
        This function generates a Google Maps directions URL.
        Format: https://www.google.com/maps/dir/current_location/destination/
        """
        doctor = obj.time_slot.doctor
        
        # Only generate a link if the doctor has set their coordinates
        if doctor.latitude and doctor.longitude:
            # Use the Google Maps dir format: /dir/origin/destination/
            # Using empty origin so Maps will use current location
            destination = f"{doctor.latitude},{doctor.longitude}"
            
            # Generate the proper Google Maps directions URL
            base_url = "https://www.google.com/maps/dir/"
            # Add current location placeholder (empty) and destination
            directions_url = f"{base_url}Current+Location/{destination}/"
            
            return directions_url
        
        # If no coordinates, return None so the frontend can hide the button
        return None
    
class DoctorSchedulePatientSerializer(serializers.ModelSerializer):
    """
    A nested serializer to show *only* the patient's public info
    for the doctor's dashboard.
    """
    full_name = serializers.SerializerMethodField()
    age = serializers.IntegerField(read_only=True)

    class Meta:
        model = Patient
        fields = ['id', 'full_name', 'phone_number', 'email', 'age']
    
    def get_full_name(self, obj):
        """
        'obj' is the Patient instance.
        """
        return f"{obj.first_name} {obj.last_name}"


class DoctorScheduleSerializer(serializers.ModelSerializer):
    """
    Main serializer for the "Doctor's Schedule" list.
    """
    # Use our new nested serializer for the patient
    patient = DoctorSchedulePatientSerializer(read_only=True)
    
    # Flatten the TimeSlot fields for easy access
    start_time = serializers.DateTimeField(source='time_slot.start_time')
    end_time = serializers.DateTimeField(source='time_slot.end_time')
    mode = serializers.CharField(source='time_slot.mode')

    # This is the NEW field for our ML Model
    no_show_prediction = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = [
            'id',
            'status',
            'start_time',
            'end_time',
            'mode',
            'patient', # The nested patient object
            'patient_notes', # The symptoms
            'no_show_prediction',
        ]

    def get_no_show_prediction(self, obj):
        """
        This function prepares data and calls the ML model.
        'obj' is the Appointment instance.
        """
        
        # 1. Prepare the features your model needs
        features = {
            'booking_date': obj.created_at.isoformat(),
            'appointment_date': obj.time_slot.start_time.isoformat(),
            'reminder_sent': obj.reminder_sent,
            'patient_age': obj.patient.age or 37, # Use 37 (your median) as a default
            # 'patient_gender' is not needed by your final model, so we leave it out
        }

        ML_SERVICE_URL = 'http://127.0.0.1:5001/predict'
        # 2. Call the ML Model API
        # (This is where you would use 'requests' or 'httpx'
        # to call your deployed ML service)
        
        # --- SIMULATION ---
        # For now, we will simulate the ML call
        # and just return a random prediction.
        try:
            response = requests.post(
                settings.ML_SERVICE_URL, # <-- USE THE SETTING
                json=features, 
                timeout=2 # Don't wait more than 2 seconds
            )
            
            # Check for a successful response
            if response.status_code == 200:
                prediction_data = response.json()
                # We return the "Low Risk" / "High Risk" label
                return prediction_data.get('prediction', 'Error')
            else:
                # The ML service returned an error (e.g., 400, 500)
                print(f"ML Service Error: {response.status_code} {response.text}")
                return "N/A"

        except requests.RequestException as e:
            # The ML service is down or unreachable
            print(f"Cannot connect to ML Service: {e}")
            return "N/A"