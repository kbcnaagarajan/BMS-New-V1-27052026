from django.contrib import admin
from .models import ProjectIssue, ProjectRisk, ChangeRequest, SupportTicket


@admin.register(ProjectIssue)
class ProjectIssueAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'issue_type', 'severity', 'status', 'assigned_to', 'created_at']
    list_filter = ['issue_type', 'severity', 'status']
    search_fields = ['title', 'project__project_name']


@admin.register(ProjectRisk)
class ProjectRiskAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'severity', 'probability', 'impact', 'risk_score', 'status', 'owner']
    list_filter = ['severity', 'probability', 'impact', 'status']
    search_fields = ['title', 'project__project_name']


@admin.register(ChangeRequest)
class ChangeRequestAdmin(admin.ModelAdmin):
    list_display = ['cr_number', 'title', 'project', 'priority', 'status', 'impact_on_cost', 'created_at']
    list_filter = ['priority', 'status']
    search_fields = ['cr_number', 'title', 'project__project_name']


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'priority', 'status', 'assigned_to', 'created_at']
    list_filter = ['priority', 'status']
    search_fields = ['title', 'project__project_name']
