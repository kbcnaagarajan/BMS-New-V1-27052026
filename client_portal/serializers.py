from rest_framework import serializers
from client_crm.models import Client, ClientContact
from project_360.models import (
    Project, ProjectMilestone, ProjectTask, ProjectDeliverable,
    ProjectStatusUpdate, ProjectDocument, ProjectActivityLog
)
from project_360.serializers import (
    ProjectMilestoneSerializer, ProjectTaskMinimalSerializer,
    ProjectDeliverableSerializer, ProjectStatusUpdateSerializer,
    ProjectDocumentSerializer, ProjectActivityLogSerializer
)
from billing.serializers import InvoiceListSerializer


class ClientPortalProjectSerializer(serializers.ModelSerializer):
    milestones = serializers.SerializerMethodField()
    tasks = serializers.SerializerMethodField()
    deliverables = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()
    status_updates = serializers.SerializerMethodField()
    team_members = serializers.SerializerMethodField()
    invoices = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ['id', 'project_code', 'project_name', 'description', 'status', 'health',
                  'completion_percentage', 'start_date', 'expected_end_date',
                  'milestones', 'tasks', 'deliverables', 'documents',
                  'status_updates', 'team_members', 'invoices']

    def get_milestones(self, obj):
        return ProjectMilestoneSerializer(obj.milestones.all(), many=True).data

    def get_tasks(self, obj):
        return ProjectTaskMinimalSerializer(obj.tasks.filter(is_client_visible=True), many=True).data

    def get_deliverables(self, obj):
        return ProjectDeliverableSerializer(obj.deliverables.all(), many=True).data

    def get_documents(self, obj):
        return ProjectDocumentSerializer(obj.project_documents.filter(is_client_visible=True), many=True).data

    def get_status_updates(self, obj):
        return ProjectStatusUpdateSerializer(obj.status_updates.filter(is_client_visible=True, is_published=True), many=True).data

    def get_team_members(self, obj):
        from project_360.serializers import ProjectTeamMemberSerializer
        return ProjectTeamMemberSerializer(
            obj.team_members.filter(is_active=True, is_client_visible=True), many=True
        ).data

    def get_invoices(self, obj):
        return InvoiceListSerializer(obj.invoices.all(), many=True).data


class ClientPortalDashboardSerializer(serializers.Serializer):
    total_projects = serializers.IntegerField()
    active_projects = serializers.IntegerField()
    completed_projects = serializers.IntegerField()
    pending_approvals = serializers.IntegerField()
    open_issues = serializers.IntegerField()
    upcoming_milestones = serializers.IntegerField()
    invoices_pending = serializers.IntegerField()
    projects = ClientPortalProjectSerializer(many=True)
