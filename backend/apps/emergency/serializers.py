from rest_framework import serializers
from apps.accounts.models import DoctorProfile
from .models import EmergencyRequest, TRIAGE_CHOICES

# --- Serializers for Step 1: Find Specialist ---

class TriageInputSerializer(serializers.Serializer):
    """
    Input: What the patient sends when they hit "Emergency".
    """
    triage_category = serializers.ChoiceField(choices=TRIAGE_CHOICES)
    patient_notes = serializers.CharField(required=False, allow_blank=True)
    user_lat = serializers.DecimalField(max_digits=9, decimal_places=6)
    user_lng = serializers.DecimalField(max_digits=9, decimal_places=6)

class SpecialistResultSerializer(serializers.ModelSerializer):
    """
    Output: The details of a single doctor in the returned list.
    """
    doctor_id = serializers.IntegerField(source='id')
    # We will fix the same 'user_full_name' bug from Phase 3
    full_name = serializers.SerializerMethodField()
    distance_km = serializers.FloatField(read_only=True) # Will be added by the view

    class Meta:
        model = DoctorProfile
        fields = ('doctor_id', 'full_name', 'specialty', 'clinic_address', 'distance_km')

    def get_full_name(self, obj):
        """
        Combines the doctor's first and last name.
        'obj' is the DoctorProfile instance.
        """
        return f"Dr. {obj.first_name} {obj.last_name}"


class TriageOutputSerializer(serializers.Serializer):
    """
    Output: The complete response for the "Find Specialist" request.
    """
    log_id = serializers.IntegerField()
    doctors = SpecialistResultSerializer(many=True)

# --- Serializers for Step 2: Request Doctor ---

class RequestDoctorInputSerializer(serializers.Serializer):
    """
    Input: The patient's choice of doctor and the log ID.
    """
    log_id = serializers.IntegerField()
    doctor_id = serializers.IntegerField()

class RequestDoctorOutputSerializer(serializers.Serializer):
    """
    Output: The final confirmation with the map link.
    """
    appointment_id = serializers.IntegerField()
    doctor_name = serializers.CharField()
    clinic_address = serializers.CharField()
    get_directions_link = serializers.CharField()
