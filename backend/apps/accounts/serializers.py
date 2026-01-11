"""
SarvSaathi - Accounts Serializers
Clean, organized serializers for user management.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from datetime import date
from dateutil.relativedelta import relativedelta

from .models import (
    CustomUser, UserProfile, DoctorProfile, 
    DoctorEducation, DoctorExperience,
    FamilyMember, EmergencyContact, MedicalRecord, OTP
)

User = get_user_model()


# =============================================================================
# AUTH SERIALIZERS
# =============================================================================

class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        min_length=6,
        style={'input_type': 'password'}
    )
    confirm_password = serializers.CharField(
        write_only=True, 
        required=False,
        style={'input_type': 'password'}
    )

    class Meta:
        model = CustomUser
        fields = ('email', 'password', 'confirm_password', 'user_type', 'first_name', 'last_name', 'phone_number')
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
            'phone_number': {'required': False},
        }

    def validate(self, data):
        # Check passwords match if confirm_password provided
        if data.get('confirm_password') and data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password', None)
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            user_type=validated_data.get('user_type', 'patient'),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone_number=validated_data.get('phone_number', ''),
        )
        return user


class RegisterWithOTPSerializer(serializers.ModelSerializer):
    """Serializer for registration with OTP verification."""
    
    password = serializers.CharField(write_only=True, required=True, min_length=6)
    otp_code = serializers.CharField(write_only=True, required=True, max_length=6, min_length=6)

    class Meta:
        model = CustomUser
        fields = ('email', 'password', 'user_type', 'otp_code', 'first_name', 'last_name', 'phone_number')

    def validate(self, data):
        email = data.get('email')
        otp_code = data.get('otp_code')

        try:
            otp = OTP.objects.filter(
                email=email,
                otp_type='email',
                is_verified=False
            ).latest('created_at')

            if not otp.is_valid():
                raise serializers.ValidationError({"otp_code": "OTP has expired. Please request a new one."})

            if otp.otp_code != otp_code:
                otp.attempts += 1
                otp.save()
                raise serializers.ValidationError({"otp_code": "Invalid OTP code."})

        except OTP.DoesNotExist:
            raise serializers.ValidationError({"otp_code": "No OTP found. Please request an OTP first."})

        return data

    def create(self, validated_data):
        otp_code = validated_data.pop('otp_code')
        
        # Mark OTP as verified
        OTP.objects.filter(
            email=validated_data['email'],
            otp_type='email'
        ).update(is_verified=True)

        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            user_type=validated_data.get('user_type', 'patient'),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone_number=validated_data.get('phone_number', ''),
            is_email_verified=True,
        )
        return user


class SendOTPSerializer(serializers.Serializer):
    """Serializer for sending OTP."""
    
    email = serializers.EmailField(required=False)
    phone_number = serializers.CharField(max_length=15, required=False)
    otp_type = serializers.ChoiceField(
        choices=['email', 'phone', 'login', 'reset_password'],
        default='email'
    )

    def validate(self, data):
        if not data.get('email') and not data.get('phone_number'):
            raise serializers.ValidationError("Either email or phone_number is required.")
        return data


class VerifyOTPSerializer(serializers.Serializer):
    """Serializer for verifying OTP."""
    
    email = serializers.EmailField(required=False)
    phone_number = serializers.CharField(max_length=15, required=False)
    otp_code = serializers.CharField(max_length=6, min_length=6)
    otp_type = serializers.ChoiceField(
        choices=['email', 'phone', 'login', 'reset_password'],
        default='email'
    )

    def validate(self, data):
        if not data.get('email') and not data.get('phone_number'):
            raise serializers.ValidationError("Either email or phone_number is required.")
        return data


# =============================================================================
# USER SERIALIZERS
# =============================================================================

class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user info for nested serialization."""
    
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'first_name', 'last_name', 'full_name', 'phone_number', 'user_type')
        read_only_fields = ('id', 'email', 'user_type')


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user extended profile."""

    class Meta:
        model = UserProfile
        fields = (
            'gender', 'blood_group',
            'address_line1', 'address_line2', 'city', 'state', 'pincode', 'country',
            'latitude', 'longitude',
            'notification_email', 'notification_sms', 'notification_push',
            'avatar_url', 'full_address'
        )
        read_only_fields = ('full_address',)


class UserDetailSerializer(serializers.ModelSerializer):
    """Complete user details including profile."""
    
    profile = UserProfileSerializer()
    full_name = serializers.CharField(read_only=True)
    age = serializers.IntegerField(read_only=True)
    is_profile_complete = serializers.BooleanField(read_only=True)

    class Meta:
        model = CustomUser
        fields = (
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'phone_number', 'date_of_birth', 'age',
            'user_type', 'is_email_verified', 'is_phone_verified',
            'is_profile_complete', 'date_joined', 'profile'
        )
        read_only_fields = ('id', 'email', 'user_type', 'date_joined')

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)
        
        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update profile fields
        if profile_data:
            profile = instance.profile
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()

        # Sync 'self' family member
        self_member = instance.family_members.filter(relationship='self').first()
        if self_member:
            self_member.first_name = instance.first_name
            self_member.last_name = instance.last_name
            self_member.phone_number = instance.phone_number
            self_member.date_of_birth = instance.date_of_birth
            self_member.save()

        return instance


# =============================================================================
# DOCTOR SERIALIZERS
# =============================================================================

class DoctorEducationSerializer(serializers.ModelSerializer):
    """Serializer for doctor education."""

    class Meta:
        model = DoctorEducation
        fields = ('id', 'degree', 'institution', 'year_of_completion')


class DoctorExperienceSerializer(serializers.ModelSerializer):
    """Serializer for doctor experience."""
    
    is_current = serializers.BooleanField(read_only=True)

    class Meta:
        model = DoctorExperience
        fields = ('id', 'hospital_name', 'position', 'start_date', 'end_date', 'description', 'is_current')


class DoctorProfileSerializer(serializers.ModelSerializer):
    """Serializer for doctor professional profile."""
    
    # User info
    user = UserBasicSerializer(read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    
    # Computed fields
    display_name = serializers.CharField(read_only=True)
    is_profile_complete = serializers.BooleanField(read_only=True)
    
    # Related data
    education = DoctorEducationSerializer(many=True, read_only=True)
    experiences = DoctorExperienceSerializer(many=True, read_only=True)

    class Meta:
        model = DoctorProfile
        fields = (
            'id', 'user', 'email', 'display_name',
            'specialty', 'sub_specialty', 'license_number', 'license_expiry',
            'years_of_experience', 'qualification',
            'clinic_name', 'clinic_address', 'clinic_latitude', 'clinic_longitude', 'clinic_phone',
            'consultation_fee', 'online_consultation_fee', 'consultation_duration',
            'is_available_for_emergency', 'is_accepting_new_patients',
            'is_verified', 'verification_date',
            'bio', 'languages',
            'total_appointments', 'total_reviews', 'average_rating',
            'is_profile_complete',
            'education', 'experiences',
            'created_at', 'updated_at'
        )
        read_only_fields = (
            'id', 'user', 'is_verified', 'verification_date', 'verified_by',
            'total_appointments', 'total_reviews', 'average_rating',
            'created_at', 'updated_at'
        )


class DoctorListSerializer(serializers.ModelSerializer):
    """Simplified doctor serializer for listing - frontend compatible."""
    
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    display_name = serializers.CharField(read_only=True)
    
    # Frontend-compatible aliases
    experience = serializers.IntegerField(source='years_of_experience', read_only=True)
    rating = serializers.DecimalField(source='average_rating', max_digits=3, decimal_places=2, read_only=True)
    reviews = serializers.IntegerField(source='total_reviews', read_only=True)
    available_today = serializers.SerializerMethodField()

    class Meta:
        model = DoctorProfile
        fields = (
            'id', 'email', 'first_name', 'last_name', 'display_name',
            'specialty', 'qualification', 
            'years_of_experience', 'experience',  # Both names for compatibility
            'consultation_fee', 'clinic_address',
            'is_verified', 'is_accepting_new_patients',
            'total_reviews', 'reviews', 'average_rating', 'rating',  # Both names
            'available_today'
        )
    
    def get_available_today(self, obj):
        """Check if doctor has available slots today."""
        from django.utils import timezone
        today = timezone.now().date()
        return obj.time_slots.filter(date=today, status='available').exists()


# =============================================================================
# FAMILY MEMBER SERIALIZERS
# =============================================================================

class FamilyMemberSerializer(serializers.ModelSerializer):
    """Serializer for family members."""
    
    full_name = serializers.CharField(read_only=True)
    age = serializers.IntegerField(read_only=True)
    is_profile_complete = serializers.BooleanField(read_only=True)

    class Meta:
        model = FamilyMember
        fields = (
            'id', 'first_name', 'last_name', 'full_name',
            'relationship', 'gender', 'date_of_birth', 'age',
            'phone_number', 'email',
            'blood_group', 'allergies', 'chronic_conditions',
            'is_active', 'is_profile_complete',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate_date_of_birth(self, value):
        if not value:
            return value

        age = relativedelta(date.today(), value).years
        relationship = self.initial_data.get('relationship') or (self.instance.relationship if self.instance else None)

        # Only enforce 18+ for 'self' records
        if relationship == 'self' and age < 18:
            raise serializers.ValidationError("Account holders must be 18 years or older.")

        return value

    def validate_relationship(self, value):
        # Prevent creating multiple 'self' records
        if value == 'self':
            user = self.context['request'].user
            existing_self = FamilyMember.objects.filter(user=user, relationship='self')
            if self.instance:
                existing_self = existing_self.exclude(pk=self.instance.pk)
            if existing_self.exists():
                raise serializers.ValidationError("You already have a 'self' profile.")
        return value


class FamilyMemberListSerializer(serializers.ModelSerializer):
    """Simplified serializer for dropdown/selection."""
    
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = FamilyMember
        fields = ('id', 'full_name', 'relationship', 'is_profile_complete')


# =============================================================================
# EMERGENCY CONTACT SERIALIZERS
# =============================================================================

class EmergencyContactSerializer(serializers.ModelSerializer):
    """Serializer for emergency contacts."""

    class Meta:
        model = EmergencyContact
        fields = ('id', 'name', 'phone_number', 'relationship', 'email', 'is_primary', 'created_at')
        read_only_fields = ('id', 'created_at')

    def validate_is_primary(self, value):
        # Only one primary contact allowed
        if value:
            user = self.context['request'].user
            existing_primary = EmergencyContact.objects.filter(user=user, is_primary=True)
            if self.instance:
                existing_primary = existing_primary.exclude(pk=self.instance.pk)
            if existing_primary.exists():
                # Auto-demote existing primary
                existing_primary.update(is_primary=False)
        return value


# =============================================================================
# MEDICAL RECORD SERIALIZERS
# =============================================================================

class MedicalRecordSerializer(serializers.ModelSerializer):
    """Serializer for medical records."""
    
    family_member_name = serializers.CharField(source='family_member.full_name', read_only=True)

    class Meta:
        model = MedicalRecord
        fields = (
            'id', 'family_member', 'family_member_name',
            'title', 'record_type', 'description', 'record_date',
            'file_url', 'file_name',
            'doctor_name', 'hospital_name',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate_family_member(self, value):
        if value and value.user != self.context['request'].user:
            raise serializers.ValidationError("Invalid family member.")
        return value


# Backward compatibility alias
PatientSerializer = FamilyMemberSerializer
