from django.contrib import admin
from .models import (
    Project, ProjectTeamMember, ProjectMilestone, ProjectTask,
    TaskComment, TaskAttachment, ProjectDeliverable, ProjectStatusUpdate,
    ProjectDocument, ProjectActivityLog, ProjectClosureChecklist
)


class ProjectTeamMemberInline(admin.TabularInline):
    model = ProjectTeamMember
    extra = 1


class ProjectMilestoneInline(admin.TabularInline):
    model = ProjectMilestone
    extra = 1


class ProjectTaskInline(admin.TabularInline):
    model = ProjectTask
    extra = 1


class ProjectDocumentInline(admin.TabularInline):
    model = ProjectDocument
    extra = 1


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['project_code', 'project_name', 'client', 'status', 'health',
                    'priority', 'project_manager', 'completion_percentage', 'start_date']
    list_filter = ['status', 'health', 'priority', 'billing_type']
    search_fields = ['project_name', 'project_code', 'client__name']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ProjectTeamMemberInline, ProjectMilestoneInline, ProjectTaskInline, ProjectDocumentInline]
    fieldsets = (
        ('Basic Information', {'fields': ('project_name', 'project_code', 'client', 'description', 'project_objectives', 'scope')}),
        ('Status', {'fields': ('status', 'health', 'priority', 'completion_percentage')}),
        ('Dates', {'fields': ('start_date', 'expected_end_date', 'actual_end_date', 'closure_date')}),
        ('Financial', {'fields': ('budget', 'currency', 'billing_type', 'is_billable', 'estimated_hours', 'actual_hours')}),
        ('Team', {'fields': ('project_manager', 'delivery_manager', 'account_manager', 'client_spoc')}),
        ('Additional', {'fields': ('project_type', 'tags', 'sow_document', 'closure_report')}),
        ('Audit', {'fields': ('created_by', 'created_at', 'updated_at')}),
    )


@admin.register(ProjectTeamMember)
class ProjectTeamMemberAdmin(admin.ModelAdmin):
    list_display = ['user', 'project', 'role', 'is_active', 'is_client_visible', 'allocation_percentage']
    list_filter = ['role', 'is_active', 'is_client_visible']
    search_fields = ['user__email', 'user__first_name', 'project__project_name']


@admin.register(ProjectMilestone)
class ProjectMilestoneAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'due_date', 'status', 'progress', 'amount']
    list_filter = ['status']
    search_fields = ['title', 'project__project_name']


@admin.register(ProjectTask)
class ProjectTaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'assigned_to', 'priority', 'status',
                    'due_date', 'progress_percentage']
    list_filter = ['status', 'priority', 'task_type']
    search_fields = ['title', 'project__project_name', 'assigned_to__email']


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    list_display = ['task', 'user', 'created_at', 'is_client_visible']
    list_filter = ['is_client_visible']


@admin.register(TaskAttachment)
class TaskAttachmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'task', 'uploaded_by', 'created_at']


@admin.register(ProjectDeliverable)
class ProjectDeliverableAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'milestone', 'status', 'due_date', 'submitted_date', 'client_approved']
    list_filter = ['status', 'client_approved']


@admin.register(ProjectStatusUpdate)
class ProjectStatusUpdateAdmin(admin.ModelAdmin):
    list_display = ['project', 'health', 'week_start_date', 'is_published', 'created_at']
    list_filter = ['health', 'is_published']


@admin.register(ProjectDocument)
class ProjectDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'document_type', 'is_client_visible', 'uploaded_by', 'created_at']
    list_filter = ['document_type', 'is_client_visible']


@admin.register(ProjectActivityLog)
class ProjectActivityLogAdmin(admin.ModelAdmin):
    list_display = ['project', 'user', 'action_type', 'description', 'created_at']
    list_filter = ['action_type', 'created_at']
    readonly_fields = ['project', 'user', 'action_type', 'description', 'created_at']


@admin.register(ProjectClosureChecklist)
class ProjectClosureChecklistAdmin(admin.ModelAdmin):
    list_display = ['project', 'is_closed', 'closed_by', 'closed_at']
    list_filter = ['is_closed']
