from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, CooperatorRequest


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin customizado para o modelo User"""
    
    list_display = [
        'email', 'get_full_name', 'user_type', 
        'is_email_verified', 'is_active', 'created_at'
    ]
    list_filter = [
        'user_type', 'is_email_verified', 'is_active', 
        'is_staff', 'created_at'
    ]
    search_fields = ['email', 'first_name', 'last_name', 'username']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informações Adicionais', {
            'fields': (
                'user_type', 'profile_image', 'phone', 'bio', 
                'is_email_verified', 'max_cooperations'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Informações Adicionais', {
            'fields': ('email', 'first_name', 'last_name', 'user_type')
        }),
    )
    
    def get_full_name(self, obj):
        """Exibe nome completo no admin"""
        return obj.get_full_name()
    get_full_name.short_description = 'Nome Completo'


@admin.register(CooperatorRequest)
class CooperatorRequestAdmin(admin.ModelAdmin):
    """Admin para solicitações de cooperação"""
    
    list_display = [
        'cooperator', 'meeting_creator', 'status', 
        'created_at', 'updated_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = [
        'cooperator__email', 'cooperator__first_name', 
        'meeting_creator__email', 'meeting_creator__first_name'
    ]
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {
            'fields': ('cooperator', 'meeting_creator', 'status', 'message')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

# Register your models here.
