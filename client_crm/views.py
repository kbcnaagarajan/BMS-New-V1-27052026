from rest_framework import viewsets, status, generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from .models import Client, ClientContact, ClientLocation, ClientContract, ClientNote, ClientCommunicationLog
from .serializers import (
    ClientListSerializer, ClientDetailSerializer, ClientContactSerializer,
    ClientLocationSerializer, ClientContractSerializer, ClientNoteSerializer,
    ClientCommunicationLogSerializer
)
from project_360.models import Project
from user_management.mixins import CompanyScopeMixin


class ClientViewSet(CompanyScopeMixin, viewsets.ModelViewSet):
    queryset = Client.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'client_type', 'industry', 'country']
    search_fields = ['name', 'client_code', 'email', 'phone']

    def get_serializer_class(self):
        if self.action == 'list':
            return ClientListSerializer
        return ClientDetailSerializer

    @action(detail=True, methods=['get'])
    def projects(self, request, pk=None):
        client = self.get_object()
        projects = self.filter_by_company(Project.objects.all()).filter(client=client)
        from project_360.serializers import ProjectListSerializer
        serializer = ProjectListSerializer(projects, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def dashboard(self, request, pk=None):
        client = self.get_object()
        projects = self.filter_by_company(Project.objects.all()).filter(client=client)
        active_projects = projects.filter(status__in=['active', 'kickoff_scheduled'])
        completed_projects = projects.filter(status='completed')
        total_invoices = sum(
            invoice.amount for project in projects
            for invoice in project.invoices.all()
        )
        total_paid = sum(
            payment.amount for project in projects
            for invoice in project.invoices.all()
            for payment in invoice.payments.all()
        )
        return Response({
            'client_name': client.name,
            'total_projects': projects.count(),
            'active_projects': active_projects.count(),
            'completed_projects': completed_projects.count(),
            'total_invoice_amount': float(total_invoices),
            'total_paid_amount': float(total_paid),
            'outstanding_amount': float(total_invoices - total_paid),
            'open_issues': sum(
                project.issues.filter(status__in=['open', 'in_progress']).count()
                for project in projects
            ),
        })


class ClientContactViewSet(CompanyScopeMixin, viewsets.ModelViewSet):
    queryset = ClientContact.objects.all()
    serializer_class = ClientContactSerializer
    filterset_fields = ['client', 'is_primary', 'can_login']
    search_fields = ['first_name', 'last_name', 'email']


class ClientLocationViewSet(CompanyScopeMixin, viewsets.ModelViewSet):
    queryset = ClientLocation.objects.all()
    serializer_class = ClientLocationSerializer
    filterset_fields = ['client', 'is_headquarters']


class ClientContractViewSet(CompanyScopeMixin, viewsets.ModelViewSet):
    queryset = ClientContract.objects.all()
    serializer_class = ClientContractSerializer
    filterset_fields = ['client', 'status']


class ClientNoteViewSet(CompanyScopeMixin, viewsets.ModelViewSet):
    queryset = ClientNote.objects.all()
    serializer_class = ClientNoteSerializer
    filterset_fields = ['client', 'is_client_visible']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ClientCommunicationLogViewSet(CompanyScopeMixin, viewsets.ModelViewSet):
    queryset = ClientCommunicationLog.objects.all()
    serializer_class = ClientCommunicationLogSerializer
    filterset_fields = ['client', 'communication_type', 'direction']

    def perform_create(self, serializer):
        serializer.save(communicated_by=self.request.user)
