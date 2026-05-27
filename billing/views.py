from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Sum
from user_management.mixins import CompanyScopeMixin
from .models import BillingMilestone, Invoice, Payment
from .serializers import (
    BillingMilestoneSerializer, InvoiceSerializer, InvoiceListSerializer, PaymentSerializer
)


class BillingMilestoneViewSet(CompanyScopeMixin, viewsets.ModelViewSet):
    queryset = BillingMilestone.objects.all()
    serializer_class = BillingMilestoneSerializer
    filterset_fields = ['project', 'status']


class InvoiceViewSet(CompanyScopeMixin, viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    filterset_fields = ['client', 'project', 'status']
    search_fields = ['invoice_number', 'client__name', 'project__project_name']

    def get_serializer_class(self):
        if self.action == 'list':
            return InvoiceListSerializer
        return InvoiceSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_sent(self, request, pk=None):
        invoice = self.get_object()
        invoice.status = 'sent'
        invoice.save()
        return Response(InvoiceSerializer(invoice).data)

    @action(detail=True, methods=['post'])
    def record_payment(self, request, pk=None):
        invoice = self.get_object()
        serializer = PaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = serializer.save(
            invoice=invoice,
            project=invoice.project,
            client=invoice.client,
            received_by=request.user
        )
        invoice.paid_amount = (invoice.paid_amount or 0) + payment.amount
        invoice.balance_amount = invoice.total_amount - invoice.paid_amount
        if invoice.balance_amount <= 0:
            invoice.status = 'paid'
        elif invoice.paid_amount > 0:
            invoice.status = 'partial'
        invoice.save()
        return Response(InvoiceSerializer(invoice).data)


class PaymentViewSet(CompanyScopeMixin, viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    filterset_fields = ['invoice', 'client', 'project', 'payment_mode']
    ordering = ['-payment_date']
