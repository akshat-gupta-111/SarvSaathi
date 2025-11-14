from rest_framework import serializers
from django.utils import timezone
from django.conf import settings

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
    A WRITE-ONLY serializer for DOCTORS to create their availability.
    """
    class Meta:
        model = TimeSlot
        # We only need these fields from the doctor.
        # The 'doctor' field itself will be set automatically from the logged-in user.
        fields = ('start_time', 'end_time', 'mode')

    def validate(self, data):
        """
        Check that start_time is before end_time and not in the past.
        """
        if data['start_time'] >= data['end_time']:
            raise serializers.ValidationError("End time must be after start time.")
        
        if data['start_time'] < timezone.now():
            raise serializers.ValidationError("Cannot create time slots in the past.")
        
        return data

# --- Serializer 4 (Phase 2): For Patient to START a booking ---

class AppointmentCreateSerializer(serializers.Serializer):
    """
    This serializer is used ONLY to validate the patient's
    INPUT when they start a booking. It just takes a time_slot_id.
    """
    # This is the only field the patient needs to send.
    time_slot_id = serializers.IntegerField()

    def validate_time_slot_id(self, value):
        # Check 1: Does this TimeSlot even exist?
        try:
            time_slot = TimeSlot.objects.get(id=value)
        except TimeSlot.DoesNotExist:
            raise serializers.ValidationError("This time slot does not exist.")
        
        # Check 2: Is it still available?
        if not time_slot.is_available:
            raise serializers.ValidationError("This time slot is no longer available.")
            
        # Check 3: Is it in the past?
        if time_slot.start_time < timezone.now():
            raise serializers.ValidationError("This time slot is in the past.")

        # The 'value' is just an ID. We'll pass the actual
        # 'time_slot' object to the view by attaching it here.
        self.context['time_slot'] = time_slot
        return value

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