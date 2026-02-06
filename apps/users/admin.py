from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email_display', 'username', 'first_name', 'last_name', 'is_staff', 'profile_visibility')
    search_fields = ('username', 'first_name', 'last_name', 'email_hash')
    ordering = ('username',)
    readonly_fields = ('email_hash', 'phone_hash', 'created_at', 'updated_at')
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Public Profile', {'fields': ('username', 'first_name', 'last_name', 'avatar')}),
        ('Privacy Settings', {
            'fields': ('profile_visibility', 'email_visibility', 'activity_visibility'),
            'description': 'Control who can see this user\'s information'
        }),
        ('Contact Information', {
            'fields': ('phone',),
            'description': 'Phone number is stored in plain text. Use hashed value for privacy.'
        }),
        ('Security', {
            'fields': ('email_hash', 'phone_hash', 'last_password_change', 'password_reset_required'),
            'description': 'Email and phone hashes for GDPR compliance. Read-only.',
            'classes': ('collapse',)
        }),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_staff', 'is_active', 'username')}
        ),
    )

    def email_display(self, obj):
        """
        Display email safely - show masked version in list view.
        Full email only visible in detail view for staff.
        """
        if obj.email:
            parts = obj.email.split('@')
            masked = f"{parts[0][:2]}***@{parts[1]}"
            return format_html(
                '<span title="Email: {}">{}</span>',
                obj.email,
                masked
            )
        return "—"
    
    email_display.short_description = 'Email (hover for full)'

    def get_readonly_fields(self, request, obj=None):
        """Make email hash and phone hash read-only."""
        readonly = list(super().get_readonly_fields(request, obj))
        if obj:  # Editing existing object
            readonly.extend(['email_hash', 'phone_hash'])
        return readonly

    def save_model(self, request, obj, form, change):
        """Auto-generate hashes when saving."""
        from .utils.privacy import hash_email, hash_phone
        
        if obj.email and (not obj.email_hash or not change):
            obj.email_hash = hash_email(obj.email)
        
        if obj.phone and (not obj.phone_hash or not change):
            obj.phone_hash = hash_phone(obj.phone)
        
        super().save_model(request, obj, form, change)