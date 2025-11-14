from django.contrib import admin
from .models import TimeSlot, Appointment

@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    """
    Admin configuration for the TimeSlot model.
    """
    # Show these fields in the admin list
    list_display = (
        '__str__',  # This will show our human-readable string
        'doctor', 
        'start_time', 
        'mode', 
        'is_available'
    )
    
    # Add filters on the right-hand side
    list_filter = ('doctor', 'mode', 'is_available')
    
    # Make 'is_available' editable directly from the list
    list_editable = ('is_available',)
    
    # Add search capability
    search_fields = ('doctor__first_name', 'doctor__last_name', 'doctor__user__email')

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Appointment model.
    """
    list_display = (
        '__str__', # Shows "Apt for John Doe (CONFIRMED)"
        'patient', 
        'get_doctor', # A custom helper method
        'status', 
        'payment_status',
        'created_at', # The 'booking_date'
    )
    
    list_filter = ('status', 'payment_status', 'time_slot__mode')
    
    search_fields = (
        'patient__first_name', 
        'patient__last_name', 
        'time_slot__doctor__first_name'
    )
    
    # Make the admin page faster by not loading patient/doctor details
    # with thousands of options in dropdowns. 'raw_id_fields' gives
    # a simple text box with a search popup.
    raw_id_fields = ('patient', 'time_slot')

    # Helper function to get the Doctor's name from the TimeSlot
    @admin.display(description='Doctor', ordering='time_slot__doctor')
    def get_doctor(self, obj):
        if obj.time_slot:
            return obj.time_slot.doctor
        return "N/A"