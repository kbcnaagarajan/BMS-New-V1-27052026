from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from user_management.mixins import CompanyScopeMixin
from .models import ProjectIssue, ProjectRisk, ChangeRequest, SupportTicket
from .serializers import (
    ProjectIssueSerializer, ProjectRiskSerializer,
    ChangeRequestSerializer, SupportTicketSerializer
)


class ProjectIssueViewSet(CompanyScopeMixin, viewsets.ModelViewSet):
    queryset = ProjectIssue.objects.all()
    serializer_class = ProjectIssueSerializer
    filterset_fields = ['project', 'issue_type', 'severity', 'status', 'assigned_to']
    search_fields = ['title', 'description']

    def perform_create(self, serializer):
        serializer.save(raised_by=self.request.user)

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        issue = self.get_object()
        issue.status = 'resolved'
        issue.resolution = request.data.get('resolution', '')
        issue.resolved_by = request.user
        issue.resolved_at = timezone.now()
        issue.save()
        return Response(ProjectIssueSerializer(issue).data)


class ProjectRiskViewSet(CompanyScopeMixin, viewsets.ModelViewSet):
    queryset = ProjectRisk.objects.all()
    serializer_class = ProjectRiskSerializer
    filterset_fields = ['project', 'severity', 'status', 'owner']
    search_fields = ['title', 'description']

    def perform_create(self, serializer):
        serializer.save(identified_by=self.request.user)

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        risk = self.get_object()
        risk.status = 'closed'
        risk.closed_date = timezone.now()
        risk.save()
        return Response(ProjectRiskSerializer(risk).data)


class ChangeRequestViewSet(CompanyScopeMixin, viewsets.ModelViewSet):
    queryset = ChangeRequest.objects.all()
    serializer_class = ChangeRequestSerializer
    filterset_fields = ['project', 'priority', 'status']
    search_fields = ['cr_number', 'title']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        cr = self.get_object()
        cr.status = 'approved'
        cr.approved_by = request.user
        cr.approved_amount = request.data.get('approved_amount', cr.impact_on_cost)
        cr.save()
        return Response(ChangeRequestSerializer(cr).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        cr = self.get_object()
        cr.status = 'rejected'
        cr.save()
        return Response(ChangeRequestSerializer(cr).data)


class SupportTicketViewSet(CompanyScopeMixin, viewsets.ModelViewSet):
    queryset = SupportTicket.objects.all()
    serializer_class = SupportTicketSerializer
    filterset_fields = ['project', 'priority', 'status', 'assigned_to']
    search_fields = ['title', 'description']

    def perform_create(self, serializer):
        serializer.save(submitted_by=self.request.user)

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        ticket = self.get_object()
        ticket.status = 'resolved'
        ticket.resolution = request.data.get('resolution', '')
        ticket.resolved_by = request.user
        ticket.resolved_at = timezone.now()
        ticket.save()
        return Response(SupportTicketSerializer(ticket).data)
