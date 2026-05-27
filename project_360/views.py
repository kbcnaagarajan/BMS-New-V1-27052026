from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Sum, Q
from django.utils import timezone
from user_management.mixins import CompanyScopeMixin
from .models import (
    Project, ProjectTeamMember, ProjectMilestone, ProjectTask,
    TaskComment, TaskAttachment, ProjectDeliverable, ProjectStatusUpdate,
    ProjectDocument, ProjectActivityLog, ProjectClosureChecklist
)
from .serializers import (
    ProjectListSerializer, ProjectDetailSerializer, ProjectTeamMemberSerializer,
    ProjectMilestoneSerializer, ProjectTaskSerializer, ProjectTaskMinimalSerializer,
    TaskCommentSerializer, TaskAttachmentSerializer, ProjectDeliverableSerializer,
    ProjectStatusUpdateSerializer, ProjectDocumentSerializer, ProjectActivityLogSerializer,
    ProjectClosureChecklistSerializer
)
from .filters import ProjectFilter


class ProjectViewSet(CompanyScopeMixin, viewsets.ModelViewSet):
    queryset = Project.objects.all()
    filterset_class = ProjectFilter
    search_fields = ['project_name', 'project_code', 'client__name', 'description']

    def get_serializer_class(self):
        if self.action == 'list':
            return ProjectListSerializer
        return ProjectDetailSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['get'])
    def dashboard(self, request, pk=None):
        project = self.get_object()
        tasks = project.tasks.all()
        return Response({
            'project_name': project.project_name,
            'health': project.health,
            'status': project.status,
            'completion': float(project.completion_percentage),
            'total_tasks': tasks.count(),
            'completed_tasks': tasks.filter(status='completed').count(),
            'in_progress_tasks': tasks.filter(status='in_progress').count(),
            'pending_tasks': tasks.filter(status__in=['new', 'assigned']).count(),
            'blocked_tasks': tasks.filter(status='blocked').count(),
            'overdue_tasks': tasks.filter(
                due_date__lt=timezone.now().date(),
                status__in=['new', 'assigned', 'in_progress']
            ).count(),
            'team_size': project.team_members.filter(is_active=True).count(),
            'open_issues': project.project_issues.filter(
                status__in=['open', 'in_progress']
            ).count() if hasattr(project, 'project_issues') else 0,
        })

    @action(detail=True, methods=['get'])
    def task_board(self, request, pk=None):
        project = self.get_object()
        tasks = project.tasks.all()
        return Response({
            'new': ProjectTaskMinimalSerializer(tasks.filter(status='new'), many=True).data,
            'assigned': ProjectTaskMinimalSerializer(tasks.filter(status='assigned'), many=True).data,
            'in_progress': ProjectTaskMinimalSerializer(tasks.filter(status='in_progress'), many=True).data,
            'blocked': ProjectTaskMinimalSerializer(tasks.filter(status='blocked'), many=True).data,
            'internal_review': ProjectTaskMinimalSerializer(tasks.filter(status='internal_review'), many=True).data,
            'client_review': ProjectTaskMinimalSerializer(tasks.filter(status='client_review'), many=True).data,
            'completed': ProjectTaskMinimalSerializer(tasks.filter(status='completed'), many=True).data,
        })


class ProjectTeamMemberViewSet(CompanyScopeMixin, viewsets.ModelViewSet):
    queryset = ProjectTeamMember.objects.all()
    serializer_class = ProjectTeamMemberSerializer
    filterset_fields = ['project', 'user', 'role', 'is_active', 'is_client_visible']


class ProjectMilestoneViewSet(CompanyScopeMixin, viewsets.ModelViewSet):
    queryset = ProjectMilestone.objects.all()
    serializer_class = ProjectMilestoneSerializer
    filterset_fields = ['project', 'status']


class ProjectTaskViewSet(CompanyScopeMixin, viewsets.ModelViewSet):
    queryset = ProjectTask.objects.all()
    serializer_class = ProjectTaskSerializer
    filterset_fields = ['project', 'milestone', 'assigned_to', 'status', 'priority', 'task_type']
    search_fields = ['title', 'description']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def update_progress(self, request, pk=None):
        task = self.get_object()
        progress = request.data.get('progress_percentage')
        status_val = request.data.get('status')
        if progress is not None:
            task.progress_percentage = progress
        if status_val:
            task.status = status_val
        if status_val == 'completed':
            task.completed_date = timezone.now()
        task.save()
        return Response(ProjectTaskSerializer(task).data)


class TaskCommentViewSet(CompanyScopeMixin, viewsets.ModelViewSet):
    queryset = TaskComment.objects.all()
    serializer_class = TaskCommentSerializer
    filterset_fields = ['task']

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TaskAttachmentViewSet(CompanyScopeMixin, viewsets.ModelViewSet):
    queryset = TaskAttachment.objects.all()
    serializer_class = TaskAttachmentSerializer
    filterset_fields = ['task']

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


class ProjectDeliverableViewSet(CompanyScopeMixin, viewsets.ModelViewSet):
    queryset = ProjectDeliverable.objects.all()
    serializer_class = ProjectDeliverableSerializer
    filterset_fields = ['project', 'milestone', 'status', 'client_approved']


class ProjectStatusUpdateViewSet(CompanyScopeMixin, viewsets.ModelViewSet):
    queryset = ProjectStatusUpdate.objects.all()
    serializer_class = ProjectStatusUpdateSerializer
    filterset_fields = ['project', 'health', 'is_published']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ProjectDocumentViewSet(CompanyScopeMixin, viewsets.ModelViewSet):
    queryset = ProjectDocument.objects.all()
    serializer_class = ProjectDocumentSerializer
    filterset_fields = ['project', 'document_type', 'is_client_visible']

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


class ProjectActivityLogViewSet(CompanyScopeMixin, viewsets.ModelViewSet):
    queryset = ProjectActivityLog.objects.all()
    serializer_class = ProjectActivityLogSerializer
    filterset_fields = ['project', 'action_type']
    ordering = ['-created_at']


class ProjectClosureChecklistViewSet(CompanyScopeMixin, viewsets.ModelViewSet):
    queryset = ProjectClosureChecklist.objects.all()
    serializer_class = ProjectClosureChecklistSerializer
    filterset_fields = ['project', 'is_closed']
