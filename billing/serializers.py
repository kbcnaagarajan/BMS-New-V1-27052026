from rest_framework import serializers
from .models import BillingMilestone, Invoice, Payment


class BillingMilestoneSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.project_name', read_only=True)

    class Meta:
        model = BillingMilestone
        fields = '__all__'


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class InvoiceSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    project_name = serializers.CharField(source='project.project_name', read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)

    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at']


class InvoiceListSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    project_name = serializers.CharField(source='project.project_name', read_only=True)

    class Meta:
        model = Invoice
        fields = ['id', 'invoice_number', 'client', 'client_name', 'project', 'project_name',
                  'invoice_date', 'due_date', 'total_amount', 'paid_amount', 'balance_amount', 'status']
