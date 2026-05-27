from rest_framework import serializers
from .models import (
    Project, ProjectTeamMember, ProjectMilestone, ProjectTask,
    TaskComment, TaskAttachment, ProjectDeliverable, ProjectStatusUpdate,
    ProjectDocument, ProjectActivityLog, ProjectClosureChecklist
)
from user_management.serializers import UserMinimalSerializer


class ProjectTeamMemberSerializer(serializers.ModelSerializer):
    user_details = UserMinimalSerializer(source='user', read_only=True)
    reporting_manager_name = serializers.SerializerMethodField()

    class Meta:
        model = ProjectTeamMember
        fields = '__all__'

    def get_reporting_manager_name(self, obj):
        if obj.reporting_manager:
            return obj.reporting_manager.full_name
        return ''


class ProjectMilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectMilestone
        fields = '__all__'


class TaskCommentSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = TaskComment
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']

    def get_user_name(self, obj):
        return obj.user.full_name


class TaskAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskAttachment
        fields = '__all__'
        read_only_fields = ['uploaded_by', 'created_at']


class ProjectTaskSerializer(serializers.ModelSerializer):
    assigned_to_details = UserMinimalSerializer(source='assigned_to', read_only=True)
    comments = TaskCommentSerializer(many=True, read_only=True)
    attachments = TaskAttachmentSerializer(many=True, read_only=True)
    milestone_title = serializers.CharField(source='milestone.title', read_only=True)

    class Meta:
        model = ProjectTask
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at']


class ProjectTaskMinimalSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.SerializerMethodField()

    class Meta:
        model = ProjectTask
        fields = ['id', 'title', 'status', 'priority', 'assigned_to',
                  'assigned_to_name', 'due_date', 'progress_percentage']

    def get_assigned_to_name(self, obj):
        return obj.assigned_to.full_name if obj.assigned_to else ''


class ProjectDeliverableSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectDeliverable
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at']


class ProjectStatusUpdateSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ProjectStatusUpdate
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at']

    def get_created_by_name(self, obj):
        return obj.created_by.full_name if obj.created_by else ''


class ProjectDocumentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ProjectDocument
        fields = '__all__'
        read_only_fields = ['uploaded_by', 'created_at']

    def get_uploaded_by_name(self, obj):
        return obj.uploaded_by.full_name if obj.uploaded_by else ''


class ProjectActivityLogSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = ProjectActivityLog
        fields = '__all__'
        read_only_fields = ['created_at']

    def get_user_name(self, obj):
        return obj.user.full_name if obj.user else 'System'


class ProjectClosureChecklistSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectClosureChecklist
        fields = '__all__'


class ProjectListSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    project_manager_name = serializers.SerializerMethodField()
    team_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ['id', 'project_code', 'project_name', 'client', 'client_name',
                  'status', 'health', 'priority', 'project_manager', 'project_manager_name',
                  'start_date', 'expected_end_date', 'completion_percentage',
                  'budget', 'team_count', 'created_at']

    def get_project_manager_name(self, obj):
        return obj.project_manager.full_name if obj.project_manager else ''

    def get_team_count(self, obj):
        return obj.team_members.filter(is_active=True).count()


class ProjectDetailSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    client_code = serializers.CharField(source='client.client_code', read_only=True)
    project_manager_name = serializers.SerializerMethodField()
    delivery_manager_name = serializers.SerializerMethodField()
    account_manager_name = serializers.SerializerMethodField()

    team_members = ProjectTeamMemberSerializer(many=True, read_only=True)
    milestones = ProjectMilestoneSerializer(many=True, read_only=True)
    tasks = ProjectTaskMinimalSerializer(many=True, read_only=True)
    deliverables = ProjectDeliverableSerializer(many=True, read_only=True)
    documents = ProjectDocumentSerializer(many=True, read_only=True)
    status_updates = ProjectStatusUpdateSerializer(many=True, read_only=True)
    activity_logs = ProjectActivityLogSerializer(many=True, read_only=True)
    closure_checklist = ProjectClosureChecklistSerializer(read_only=True)

    class Meta:
        model = Project
        fields = '__all__'

    def get_project_manager_name(self, obj):
        return obj.project_manager.full_name if obj.project_manager else ''

    def get_delivery_manager_name(self, obj):
        return obj.delivery_manager.full_name if obj.delivery_manager else ''

    def get_account_manager_name(self, obj):
        return obj.account_manager.full_name if obj.account_manager else ''
