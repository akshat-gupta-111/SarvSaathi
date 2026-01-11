"""
SarvSaathi - Accounts Admin
Admin configuration for all account-related models.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, UserProfile, DoctorProfile, 
    DoctorEducation, DoctorExperience,
    FamilyMember, EmergencyContact, MedicalRecord, OTP
)


# =============================================================================
# CUSTOM USER ADMIN
# =============================================================================

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Admin for the custom user model."""
    model = CustomUser
    
    list_display = (
        'email', 
        'first_name', 
        'last_name',
        'user_type', 
        'is_email_verified',
        'is_active',
        'date_joined',
    )
    list_filter = ('user_type', 'is_email_verified', 'is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone_number', 'user_type')}),
        ('Verification', {'fields': ('is_email_verified', 'is_phone_verified')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'user_type', 'is_staff'),
        }),
    )
    
    filter_horizontal = ('groups', 'user_permissions',)
    readonly_fields = ('date_joined', 'last_login')


# =============================================================================
# USER PROFILE ADMIN
# =============================================================================

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin for extended user profiles."""
    list_display = ('user_email', 'gender', 'blood_group', 'city', 'is_profile_complete')
    list_filter = ('gender', 'blood_group')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'city')
    raw_id_fields = ('user',)
    
    @admin.display(ordering='user__email', description='Email')
    def user_email(self, obj):
        return obj.user.email
    
    @admin.display(boolean=True, description='Complete')
    def is_profile_complete(self, obj):
        return obj.user.is_profile_complete


# =============================================================================
# DOCTOR PROFILE ADMIN
# =============================================================================

class DoctorEducationInline(admin.TabularInline):
    """Inline for doctor education."""
    model = DoctorEducation
    extra = 1


class DoctorExperienceInline(admin.TabularInline):
    """Inline for doctor experience."""
    model = DoctorExperience
    extra = 1


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    """Admin for doctor profiles."""
    list_display = (
        'user_email',
        'specialty',
        'license_number',
        'years_of_experience',
        'consultation_fee',
        'average_rating',
        'total_appointments',
        'is_verified',
    )
    list_filter = ('is_verified', 'specialty', 'is_accepting_new_patients')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'specialty', 'license_number')
    list_editable = ('is_verified',)
    raw_id_fields = ('user',)
    inlines = [DoctorEducationInline, DoctorExperienceInline]
    
    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Professional Info', {'fields': ('specialty', 'license_number', 'years_of_experience', 'bio')}),
        ('Clinic Info', {'fields': ('clinic_name', 'clinic_address', 'clinic_phone')}),
        ('Consultation', {'fields': ('consultation_fee', 'online_consultation_fee', 'consultation_duration', 'is_accepting_new_patients')}),
        ('Statistics', {'fields': ('total_appointments', 'average_rating', 'total_reviews'), 'classes': ('collapse',)}),
        ('Location', {'fields': ('clinic_latitude', 'clinic_longitude')}),
        ('Verification', {'fields': ('is_verified',)}),
    )
    
    readonly_fields = ('total_appointments', 'average_rating', 'total_reviews')
    
    @admin.display(ordering='user__email', description='Email')
    def user_email(self, obj):
        return obj.user.email


# =============================================================================
# FAMILY MEMBER ADMIN
# =============================================================================

@admin.register(FamilyMember)
class FamilyMemberAdmin(admin.ModelAdmin):
    """Admin for family members (patients)."""
    list_display = (
        '__str__',
        'user_email',
        'relationship',
        'gender',
        'blood_group',
        'is_active',
    )
    list_filter = ('relationship', 'gender', 'blood_group', 'is_active')
    search_fields = ('first_name', 'last_name', 'user__email', 'phone_number')
    raw_id_fields = ('user',)
    
    @admin.display(ordering='user__email', description='Account Owner')
    def user_email(self, obj):
        return obj.user.email


# =============================================================================
# EMERGENCY CONTACT ADMIN
# =============================================================================

@admin.register(EmergencyContact)
class EmergencyContactAdmin(admin.ModelAdmin):
    """Admin for emergency contacts."""
    list_display = ('name', 'user_email', 'relationship', 'phone_number', 'is_primary')
    list_filter = ('relationship', 'is_primary')
    search_fields = ('name', 'phone_number', 'user__email')
    raw_id_fields = ('user',)
    
    @admin.display(ordering='user__email', description='User')
    def user_email(self, obj):
        return obj.user.email


# =============================================================================
# MEDICAL RECORD ADMIN
# =============================================================================

@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    """Admin for medical records."""
    list_display = ('title', 'user_email', 'record_type', 'record_date', 'created_at')
    list_filter = ('record_type', 'record_date')
    search_fields = ('title', 'user__email', 'description')
    raw_id_fields = ('user',)
    date_hierarchy = 'record_date'
    
    @admin.display(ordering='user__email', description='User')
    def user_email(self, obj):
        return obj.user.email


# =============================================================================
# OTP ADMIN
# =============================================================================

@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    """Admin for OTP records."""
    list_display = ('email', 'phone_number', 'otp_type', 'is_verified', 'created_at', 'expires_at')
    list_filter = ('otp_type', 'is_verified')
    search_fields = ('email', 'phone_number')
    readonly_fields = ('otp_code', 'created_at')
    ordering = ('-created_at',)
