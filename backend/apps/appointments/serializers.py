from rest_framework import serializers
from .models import TimeSlot, Appointment
from apps.accounts.models import DoctorProfile

# --- Serializer 1: For the Patient to READ slot info ---

class NestedDoctorSerializer(serializers.ModelSerializer):
    """
    A small, read-only serializer to show basic doctor info 
    inside the TimeSlotListSerializer.
    """
    class Meta:
        model = DoctorProfile
        # We only expose the fields a patient needs to see
        fields = ('first_name', 'last_name', 'specialty')

class TimeSlotListSerializer(serializers.ModelSerializer):
    """
    A READ-ONLY serializer for patients to browse available time slots.
    It includes nested doctor information.
    """
    # This 'doctor' field uses the serializer we defined above
    doctor = NestedDoctorSerializer(read_only=True)
    
    class Meta:
        model = TimeSlot
        # These are the fields the patient will see
        fields = (
            'id', 
            'doctor', 
            'start_time', 
            'end_time', 
            'mode'
        )
        read_only_fields = fields # Make all fields read-only


# --- Serializer 2: For the Doctor to CREATE slots ---

class TimeSlotSerializer(serializers.ModelSerializer):
    """
    A WRITEABLE serializer for doctors to create and manage their 
    own time slots.
    """
    
    # We make 'doctor' read-only because we will set it
    # automatically in the view, based on the logged-in user.
    # This prevents a doctor from accidentally creating a slot
    # for another doctor.
    doctor = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = TimeSlot
        fields = (
            'id', 
            'doctor', 
            'start_time', 
            'end_time', 
            'mode',
            'is_available', # We include this so a doctor can see it
        )
        
    def validate(self, data):
        """
        Add validation to ensure end_time is after start_time.
        """
        if data.get('start_time') and data.get('end_time'):
            if data['end_time'] <= data['start_time']:
                raise serializers.ValidationError("End time must be after start time.")
        return data

# --- Serializer 3: For Booking (We will build this in Phase 2) ---
# We will create the AppointmentSerializer in a later step
# when we build the booking API.