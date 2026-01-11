"""
SarvSaathi - Appointments Admin
Admin configuration for all appointment-related models.
"""

from django.contrib import admin
from .models import TimeSlot, Appointment, AppointmentStatusLog, Review, FavoriteDoctor


# =============================================================================
# TIME SLOT ADMIN
# =============================================================================

@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    """Admin for time slots."""
    list_display = (
        '__str__',
        'doctor_name',
        'date',
        'start_time',
        'end_time',
        'mode',
        'status',
        'consultation_fee',
    )
    list_filter = ('status', 'mode', 'date', 'doctor')
    search_fields = ('doctor__user__email', 'doctor__user__first_name', 'doctor__user__last_name')
    list_editable = ('status',)
    date_hierarchy = 'date'
    raw_id_fields = ('doctor',)
    
    @admin.display(ordering='doctor__user__email', description='Doctor')
    def doctor_name(self, obj):
        return obj.doctor.user.get_full_name() or obj.doctor.user.email


# =============================================================================
# APPOINTMENT ADMIN
# =============================================================================

class AppointmentStatusLogInline(admin.TabularInline):
    """Inline for appointment status logs."""
    model = AppointmentStatusLog
    extra = 0
    readonly_fields = ('from_status', 'to_status', 'changed_by', 'notes', 'created_at')
    can_delete = False


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    """Admin for appointments."""
    list_display = (
        'appointment_number',
        'patient_name',
        'doctor_name',
        'appointment_date',
        'status',
        'payment_status',
        'amount_paid',
        'created_at',
    )
    list_filter = ('status', 'payment_status', 'time_slot__mode', 'time_slot__date')
    search_fields = (
        'appointment_number',
        'user__email',
        'user__first_name',
        'family_member__first_name',
        'doctor__user__email',
    )
    raw_id_fields = ('user', 'family_member', 'doctor', 'time_slot')
    readonly_fields = ('appointment_number', 'created_at', 'updated_at')
    inlines = [AppointmentStatusLogInline]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Appointment Info', {
            'fields': ('appointment_number', 'user', 'family_member', 'doctor', 'time_slot')
        }),
        ('Status', {
            'fields': ('status', 'payment_status', 'amount_paid', 'payment_id', 'transaction_id')
        }),
        ('Patient Info', {
            'fields': ('symptoms', 'notes_for_doctor')
        }),
        ('Doctor Info', {
            'fields': ('doctor_notes', 'prescription'),
            'classes': ('collapse',)
        }),
        ('Cancellation', {
            'fields': ('cancelled_by', 'cancellation_reason', 'cancelled_at'),
            'classes': ('collapse',)
        }),
        ('Consultation Timing', {
            'fields': ('consultation_started_at', 'consultation_ended_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    @admin.display(description='Patient')
    def patient_name(self, obj):
        if obj.family_member:
            return f"{obj.family_member.first_name} {obj.family_member.last_name}"
        return obj.user.get_full_name() or obj.user.email
    
    @admin.display(description='Doctor')
    def doctor_name(self, obj):
        return obj.doctor.user.get_full_name() or obj.doctor.user.email
    
    @admin.display(description='Date')
    def appointment_date(self, obj):
        return f"{obj.time_slot.date} {obj.time_slot.start_time}"


# =============================================================================
# REVIEW ADMIN
# =============================================================================

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Admin for reviews."""
    list_display = (
        '__str__',
        'user_email',
        'doctor_name',
        'rating',
        'created_at',
    )
    list_filter = ('rating', 'created_at')
    search_fields = ('user__email', 'doctor__user__email', 'comment')
    raw_id_fields = ('user', 'doctor', 'appointment')
    readonly_fields = ('created_at',)
    
    @admin.display(ordering='user__email', description='Patient')
    def user_email(self, obj):
        return obj.user.email
    
    @admin.display(ordering='doctor__user__email', description='Doctor')
    def doctor_name(self, obj):
        return obj.doctor.user.get_full_name() or obj.doctor.user.email


# =============================================================================
# FAVORITE DOCTOR ADMIN
# =============================================================================

@admin.register(FavoriteDoctor)
class FavoriteDoctorAdmin(admin.ModelAdmin):
    """Admin for favorite doctors."""
    list_display = ('user_email', 'doctor_name', 'created_at')
    search_fields = ('user__email', 'doctor__user__email')
    raw_id_fields = ('user', 'doctor')
    
    @admin.display(ordering='user__email', description='User')
    def user_email(self, obj):
        return obj.user.email
    
    @admin.display(ordering='doctor__user__email', description='Doctor')
    def doctor_name(self, obj):
        return obj.doctor.user.get_full_name() or obj.doctor.user.email


# =============================================================================
# STATUS LOG ADMIN (optional standalone view)
# =============================================================================

@admin.register(AppointmentStatusLog)
class AppointmentStatusLogAdmin(admin.ModelAdmin):
    """Admin for appointment status logs."""
    list_display = ('appointment', 'from_status', 'to_status', 'changed_by', 'created_at')
    list_filter = ('from_status', 'to_status', 'created_at')
    search_fields = ('appointment__appointment_number',)
    raw_id_fields = ('appointment',)
    readonly_fields = ('appointment', 'from_status', 'to_status', 'changed_by', 'notes', 'created_at')
