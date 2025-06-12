from django.contrib import admin
from .models import Category, Meeting, MeetingCooperation, MeetingParticipation, Comment, Rating

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']

@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ['title', 'responsible', 'category', 'meeting_date', 'status']
    list_filter = ['status', 'category', 'meeting_date']
    search_fields = ['title', 'responsible', 'description']

admin.site.register(MeetingCooperation)
admin.site.register(MeetingParticipation)
admin.site.register(Comment)
admin.site.register(Rating)