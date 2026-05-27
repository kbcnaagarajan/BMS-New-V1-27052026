from django.contrib import admin
from .models import Meeting, MeetingActionItem, Document, Notification


class MeetingActionItemInline(admin.TabularInline):
    model = MeetingActionItem
    extra = 1


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'meeting_type', 'meeting_date', 'start_time', 'status', 'organizer']
    list_filter = ['meeting_type', 'status', 'meeting_date']
    search_fields = ['title', 'project__project_name']
    inlines = [MeetingActionItemInline]
    filter_horizontal = ['attendees', 'client_attendees']


@admin.register(MeetingActionItem)
class MeetingActionItemAdmin(admin.ModelAdmin):
    list_display = ['description', 'meeting', 'assigned_to', 'due_date', 'status']
    list_filter = ['status']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'document_type', 'project', 'client', 'visibility', 'uploaded_by', 'created_at']
    list_filter = ['document_type', 'visibility']
    search_fields = ['title', 'project__project_name', 'client__name']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['title', 'user__email']
