# backend/apps/accounts/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
# NEW: Added 'Patient' to this import
from .models import CustomUser, DoctorProfile, Patient

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    
    # These define what's shown in the admin list
    list_display = ('email', 'user_type', 'is_staff', 'is_active',)
    list_filter = ('user_type', 'is_staff', 'is_active',)
    
    # These define the fields for editing a user
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        ('Personal Info', {'fields': ('user_type',)}),
    )
    
    # These define the fields for creating a user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password', 'user_type', 'is_staff', 'is_superuser'),
        }),
    )
    
    search_fields = ('email',)
    ordering = ('email',)
    
    # We must tell the admin that 'email' is the username field
    filter_horizontal = ('groups', 'user_permissions',)

admin.site.register(CustomUser, CustomUserAdmin)


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user_email',
        'specialty',
        'license_number',
        'is_complete',
        'is_verified',
    )
    list_filter = ('is_verified', 'specialty')
    search_fields = (
        'user__email',
        'first_name',
        'last_name',
        'specialty',
        'license_number',
    )
    list_editable = ('is_verified',)
    readonly_fields = ('is_complete',)

    @admin.display(ordering='user__email', description='Email')
    def user_email(self, obj):
        return obj.user.email

# NEW: Added this entire class to register the Patient model
@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    # What fields to show in the list view
    list_display = (
        '__str__', # This shows the model's name (e.g., "John Doe (self)")
        'account_holder_email', 
        'relationship', 
        'is_complete'
    )
    
    # What fields to filter by on the side
    list_filter = ('relationship',)
    
    # What fields you can search by
    search_fields = (
        'first_name', 
        'last_name', 
        'email', 
        'account_holder__email'
    )
    
    # This is a helper to show the account holder's email
    @admin.display(ordering='account_holder__email', description='Account Holder')
    def account_holder_email(self, obj):
        return obj.account_holder.email