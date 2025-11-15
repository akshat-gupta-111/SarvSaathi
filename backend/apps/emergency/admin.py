from django.contrib import admin
from .models import EmergencyRequest

@admin.register(EmergencyRequest)
class EmergencyRequestAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'patient', 
        'doctor', 
        'triage_category', 
        'status', 
        'created_at'
    )
    list_filter = ('status', 'triage_category')
    search_fields = ('patient__first_name', 'doctor__user__email')
    raw_id_fields = ('patient', 'doctor', 'linked_appointment')