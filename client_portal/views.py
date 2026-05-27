from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q
from client_crm.models import Client, ClientContact
from project_360.models import (
    Project, ProjectTask, ProjectDeliverable, ProjectMilestone
)
from issues_risks.models import ProjectIssue
from project_360.serializers import (
    ProjectMilestoneSerializer, ProjectTaskMinimalSerializer,
    ProjectDeliverableSerializer, ProjectStatusUpdateSerializer,
    ProjectDocumentSerializer, ProjectActivityLogSerializer
)
from issues_risks.serializers import ProjectIssueSerializer, SupportTicketSerializer
from billing.serializers import InvoiceListSerializer
from meetings_documents.serializers import MeetingSerializer, DocumentSerializer
from user_management.mixins import CompanyScopeMixin
from .serializers import ClientPortalProjectSerializer


class ClientPortalBase:
    def get_client_for_user(self, user):
        if user.is_client_user:
            contacts = ClientContact.objects.filter(portal_user=user)
            if contacts.exists():
                return contacts.first().client
        return None


class ClientPortalProjectViewSet(CompanyScopeMixin, viewsets.ReadOnlyModelViewSet, ClientPortalBase):
    serializer_class = ClientPortalProjectSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_client_user:
            client = self.get_client_for_user(user)
            if client:
                return Project.objects.filter(client=client)
            return Project.objects.none()
        # For non-client users (internal), apply company scope
        if user.company:
            return Project.objects.filter(client__company=user.company)
        return Project.objects.none()

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        user = request.user
        if user.is_client_user:
            client = self.get_client_for_user(user)
            if not client:
                return Response({'error': 'No client found'}, status=404)
            projects = Project.objects.filter(client=client)
        elif user.company:
            projects = Project.objects.filter(client__company=user.company)
        else:
            return Response({'error': 'Access denied'}, status=403)

        all_tasks = ProjectTask.objects.filter(project__in=projects)
        all_deliverables = ProjectDeliverable.objects.filter(project__in=projects)

        data = {
            'total_projects': projects.count(),
            'active_projects': projects.filter(status__in=['active', 'kickoff_scheduled']).count(),
            'completed_projects': projects.filter(status='completed').count(),
            'pending_approvals': all_deliverables.filter(client_approved=False, status='client_review').count(),
            'open_issues': ProjectIssue.objects.filter(
                project__in=projects,
                status__in=['open', 'in_progress']
            ).count(),
            'upcoming_milestones': ProjectMilestone.objects.filter(
                project__in=projects,
                status__in=['pending', 'in_progress']
            ).count(),
            'invoices_pending': sum(
                invoice.status in ['sent', 'partial']
                for project in projects
                for invoice in project.invoices.all()
            ),
            'projects': ClientPortalProjectSerializer(projects, many=True).data,
        }
        return Response(data)

    @action(detail=True, methods=['get'])
    def full_view(self, request, pk=None):
        project = self.get_object()
        return Response({
            'project': ClientPortalProjectSerializer(project).data,
            'milestones': ProjectMilestoneSerializer(project.milestones.all(), many=True).data,
            'tasks': ProjectTaskMinimalSerializer(
                project.tasks.filter(is_client_visible=True), many=True
            ).data,
            'deliverables': ProjectDeliverableSerializer(project.deliverables.all(), many=True).data,
            'documents': ProjectDocumentSerializer(
                project.project_documents.filter(is_client_visible=True), many=True
            ).data,
            'status_updates': ProjectStatusUpdateSerializer(
                project.status_updates.filter(is_client_visible=True, is_published=True), many=True
            ).data,
            'activity_logs': ProjectActivityLogSerializer(
                project.activity_logs.filter(is_client_visible=True), many=True
            ).data,
            'issues': ProjectIssueSerializer(
                project.project_issues.filter(is_client_visible=True), many=True
            ).data,
            'meetings': MeetingSerializer(
                project.meetings.filter(is_client_visible=True), many=True
            ).data,
            'invoices': InvoiceListSerializer(project.invoices.all(), many=True).data,
        })

    @action(detail=True, methods=['post'])
    def approve_deliverable(self, request, pk=None):
        project = self.get_object()
        deliverable_id = request.data.get('deliverable_id')
        try:
            deliverable = project.deliverables.get(id=deliverable_id)
            deliverable.client_approved = True
            deliverable.status = 'approved'
            deliverable.feedback = request.data.get('feedback', '')
            from django.utils import timezone
            deliverable.approved_by_client_at = timezone.now()
            deliverable.save()
            return Response(ProjectDeliverableSerializer(deliverable).data)
        except ProjectDeliverable.DoesNotExist:
            return Response({'error': 'Deliverable not found'}, status=404)
