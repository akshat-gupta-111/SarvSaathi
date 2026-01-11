"""
SarvSaathi - Appointments Serializers
Clean, organized serializers for appointment management.
"""

from rest_framework import serializers
from django.utils import timezone
from django.conf import settings
from decimal import Decimal

from .models import TimeSlot, Appointment, AppointmentStatusLog, Review, FavoriteDoctor
from apps.accounts.models import DoctorProfile, FamilyMember
from apps.accounts.serializers import DoctorListSerializer, FamilyMemberListSerializer


# =============================================================================
# TIME SLOT SERIALIZERS
# =============================================================================

class TimeSlotCreateSerializer(serializers.ModelSerializer):
    """Serializer for doctors to create time slots."""

    class Meta:
        model = TimeSlot
        fields = ('id', 'date', 'start_time', 'end_time', 'mode', 'consultation_fee')
        read_only_fields = ('id',)

    def validate(self, data):
        # Check time logic
        if data['start_time'] >= data['end_time']:
            raise serializers.ValidationError({"end_time": "End time must be after start time."})

        # Check date is not in the past
        if data['date'] < timezone.now().date():
            raise serializers.ValidationError({"date": "Cannot create slots in the past."})

        # Check for same day - time should be in future
        if data['date'] == timezone.now().date():
            if data['start_time'] <= timezone.now().time():
                raise serializers.ValidationError({"start_time": "Cannot create slots in the past."})

        return data


class TimeSlotListSerializer(serializers.ModelSerializer):
    """Serializer for listing time slots."""
    
    doctor_name = serializers.CharField(source='doctor.display_name', read_only=True)
    effective_fee = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    is_past = serializers.BooleanField(read_only=True)

    class Meta:
        model = TimeSlot
        fields = (
            'id', 'doctor', 'doctor_name',
            'date', 'start_time', 'end_time',
            'mode', 'status', 'effective_fee', 'is_past'
        )


class TimeSlotDetailSerializer(serializers.ModelSerializer):
    """Detailed time slot serializer with doctor info."""
    
    doctor = DoctorListSerializer(read_only=True)
    effective_fee = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = TimeSlot
        fields = (
            'id', 'doctor',
            'date', 'start_time', 'end_time',
            'mode', 'status', 'effective_fee',
            'created_at'
        )


# =============================================================================
# APPOINTMENT SERIALIZERS
# =============================================================================

class AppointmentCreateSerializer(serializers.Serializer):
    """
    Serializer to initiate an appointment booking.
    Takes time_slot_id and family_member_id.
    """
    
    time_slot_id = serializers.IntegerField()
    family_member_id = serializers.IntegerField(required=False)
    symptoms = serializers.CharField(required=False, allow_blank=True)
    patient_notes = serializers.CharField(required=False, allow_blank=True)
    consultation_type = serializers.ChoiceField(
        choices=['in_clinic', 'online'],
        default='in_clinic'
    )

    def validate_time_slot_id(self, value):
        try:
            time_slot = TimeSlot.objects.select_related('doctor').get(id=value)
        except TimeSlot.DoesNotExist:
            raise serializers.ValidationError("Time slot not found.")

        if time_slot.status != 'available':
            raise serializers.ValidationError("This time slot is not available.")

        if time_slot.is_past:
            raise serializers.ValidationError("Cannot book a slot in the past.")

        # Check if already has a pending/confirmed appointment
        if hasattr(time_slot, 'appointment') and time_slot.appointment.status in ['pending', 'confirmed']:
            raise serializers.ValidationError("This slot is already booked.")

        self.context['time_slot'] = time_slot
        return value

    def validate_family_member_id(self, value):
        if not value:
            return value

        user = self.context['request'].user
        try:
            family_member = FamilyMember.objects.get(id=value, user=user, is_active=True)
        except FamilyMember.DoesNotExist:
            raise serializers.ValidationError("Family member not found.")

        self.context['family_member'] = family_member
        return value

    def validate(self, data):
        user = self.context['request'].user
        time_slot = self.context.get('time_slot')

        # If no family_member_id, use 'self' family member
        if not data.get('family_member_id'):
            family_member = user.family_members.filter(relationship='self').first()
            if not family_member:
                # Auto-create self family member
                family_member = FamilyMember.objects.create(
                    user=user,
                    first_name=user.first_name or 'Self',
                    last_name=user.last_name or '',
                    relationship='self',
                    phone_number=user.phone_number or ''
                )
            self.context['family_member'] = family_member

        # Check family member has minimum info
        family_member = self.context.get('family_member')
        if family_member and not family_member.is_profile_complete:
            raise serializers.ValidationError({
                "family_member_id": "Please complete the patient's profile before booking."
            })

        return data

    def create(self, validated_data):
        user = self.context['request'].user
        time_slot = self.context['time_slot']
        family_member = self.context.get('family_member')

        # Calculate fee
        consultation_fee = time_slot.effective_fee or Decimal('0.00')

        # Create appointment
        appointment = Appointment.objects.create(
            user=user,
            family_member=family_member,
            doctor=time_slot.doctor,
            time_slot=time_slot,
            consultation_type=validated_data.get('consultation_type', 'in_clinic'),
            consultation_fee=consultation_fee,
            symptoms=validated_data.get('symptoms', ''),
            patient_notes=validated_data.get('patient_notes', ''),
            status='pending',
            payment_status='unpaid'
        )

        return appointment


class AppointmentPaymentSerializer(serializers.Serializer):
    """Serializer for initiating payment."""
    
    appointment_id = serializers.IntegerField()
    payment_method = serializers.ChoiceField(
        choices=['paypal', 'razorpay', 'cash', 'free'],
        default='paypal'
    )

    def validate_appointment_id(self, value):
        user = self.context['request'].user
        try:
            appointment = Appointment.objects.get(id=value, user=user)
        except Appointment.DoesNotExist:
            raise serializers.ValidationError("Appointment not found.")

        if appointment.status != 'pending':
            raise serializers.ValidationError("This appointment is not pending payment.")

        self.context['appointment'] = appointment
        return value


class AppointmentConfirmSerializer(serializers.Serializer):
    """Serializer for confirming payment (from PayPal callback)."""
    
    paymentId = serializers.CharField()
    PayerID = serializers.CharField()


class AppointmentListSerializer(serializers.ModelSerializer):
    """Serializer for listing appointments."""
    
    doctor_name = serializers.CharField(source='doctor.display_name', read_only=True)
    doctor_specialty = serializers.CharField(source='doctor.specialty', read_only=True)
    patient_name = serializers.CharField(read_only=True)
    family_member = FamilyMemberListSerializer(read_only=True)
    time_slot = TimeSlotListSerializer(read_only=True)

    class Meta:
        model = Appointment
        fields = (
            'id', 'appointment_number',
            'doctor', 'doctor_name', 'doctor_specialty',
            'family_member', 'patient_name',
            'time_slot', 'consultation_type',
            'status', 'payment_status',
            'consultation_fee', 'amount_paid',
            'symptoms', 'created_at'
        )


class AppointmentDetailSerializer(serializers.ModelSerializer):
    """Detailed appointment serializer."""
    
    doctor = DoctorListSerializer(read_only=True)
    family_member = FamilyMemberListSerializer(read_only=True)
    time_slot = TimeSlotDetailSerializer(read_only=True)
    patient_name = serializers.CharField(read_only=True)
    can_cancel = serializers.BooleanField(read_only=True)
    can_reschedule = serializers.BooleanField(read_only=True)

    class Meta:
        model = Appointment
        fields = (
            'id', 'appointment_number',
            'user', 'doctor', 'family_member', 'patient_name',
            'time_slot', 'consultation_type',
            'status', 'payment_status', 'payment_method',
            'consultation_fee', 'amount_paid',
            'symptoms', 'patient_notes',
            'doctor_notes', 'prescription',
            'follow_up_required', 'follow_up_date',
            'video_call_link',
            'check_in_time', 'consultation_start_time', 'consultation_end_time',
            'can_cancel', 'can_reschedule',
            'created_at', 'updated_at'
        )


class DoctorAppointmentSerializer(serializers.ModelSerializer):
    """Serializer for doctors viewing their appointments."""
    
    patient_name = serializers.CharField(read_only=True)
    patient_phone = serializers.SerializerMethodField()
    time_slot = TimeSlotListSerializer(read_only=True)

    class Meta:
        model = Appointment
        fields = (
            'id', 'appointment_number',
            'patient_name', 'patient_phone',
            'time_slot', 'consultation_type',
            'status', 'payment_status',
            'symptoms', 'patient_notes',
            'check_in_time',
            'created_at'
        )

    def get_patient_phone(self, obj):
        if obj.family_member:
            return obj.family_member.phone_number or obj.user.phone_number
        return obj.user.phone_number


class AppointmentCancelSerializer(serializers.Serializer):
    """Serializer for cancelling appointment."""
    
    cancellation_reason = serializers.ChoiceField(
        choices=['patient_request', 'emergency', 'rescheduled', 'other'],
        default='patient_request'
    )
    cancellation_notes = serializers.CharField(required=False, allow_blank=True)


class AppointmentDoctorNotesSerializer(serializers.ModelSerializer):
    """Serializer for doctors to add notes after consultation."""

    class Meta:
        model = Appointment
        fields = ('doctor_notes', 'prescription', 'follow_up_required', 'follow_up_date')


# =============================================================================
# REVIEW SERIALIZERS
# =============================================================================

class ReviewCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating reviews."""

    class Meta:
        model = Review
        fields = (
            'appointment', 'rating', 'title', 'comment',
            'wait_time_rating', 'bedside_manner_rating'
        )

    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

    def validate_appointment(self, value):
        user = self.context['request'].user
        
        if value.user != user:
            raise serializers.ValidationError("You can only review your own appointments.")
        
        if value.status != 'completed':
            raise serializers.ValidationError("You can only review completed appointments.")
        
        if hasattr(value, 'review'):
            raise serializers.ValidationError("You have already reviewed this appointment.")
        
        return value

    def create(self, validated_data):
        appointment = validated_data['appointment']
        validated_data['user'] = self.context['request'].user
        validated_data['doctor'] = appointment.doctor
        return super().create(validated_data)


class ReviewListSerializer(serializers.ModelSerializer):
    """Serializer for listing reviews."""
    
    user_name = serializers.CharField(source='user.full_name', read_only=True)

    class Meta:
        model = Review
        fields = (
            'id', 'user_name', 'rating', 'title', 'comment',
            'wait_time_rating', 'bedside_manner_rating',
            'doctor_response', 'doctor_response_at',
            'created_at'
        )


class ReviewDoctorResponseSerializer(serializers.ModelSerializer):
    """Serializer for doctors to respond to reviews."""

    class Meta:
        model = Review
        fields = ('doctor_response',)

    def update(self, instance, validated_data):
        instance.doctor_response = validated_data.get('doctor_response', '')
        instance.doctor_response_at = timezone.now()
        instance.save()
        return instance


# =============================================================================
# FAVORITE SERIALIZERS
# =============================================================================

class FavoriteDoctorSerializer(serializers.ModelSerializer):
    """Serializer for favorite doctors."""
    
    doctor = DoctorListSerializer(read_only=True)
    doctor_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = FavoriteDoctor
        fields = ('id', 'doctor', 'doctor_id', 'created_at')
        read_only_fields = ('id', 'created_at')

    def validate_doctor_id(self, value):
        try:
            doctor = DoctorProfile.objects.get(id=value, is_verified=True)
        except DoctorProfile.DoesNotExist:
            raise serializers.ValidationError("Doctor not found.")
        
        user = self.context['request'].user
        if FavoriteDoctor.objects.filter(user=user, doctor=doctor).exists():
            raise serializers.ValidationError("Doctor already in favorites.")
        
        self.context['doctor'] = doctor
        return value

    def create(self, validated_data):
        validated_data.pop('doctor_id')
        validated_data['user'] = self.context['request'].user
        validated_data['doctor'] = self.context['doctor']
        return super().create(validated_data)


# =============================================================================
# APPOINTMENT STATUS LOG SERIALIZER
# =============================================================================

class AppointmentStatusLogSerializer(serializers.ModelSerializer):
    """Serializer for appointment status logs."""
    
    changed_by_name = serializers.CharField(source='changed_by.full_name', read_only=True)

    class Meta:
        model = AppointmentStatusLog
        fields = ('id', 'from_status', 'to_status', 'changed_by_name', 'notes', 'created_at')
