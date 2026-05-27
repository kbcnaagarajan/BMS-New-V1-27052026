from rest_framework import serializers


class DashboardSummarySerializer(serializers.Serializer):
    total_clients = serializers.IntegerField()
    total_projects = serializers.IntegerField()
    active_projects = serializers.IntegerField()
    completed_projects = serializers.IntegerField()
    total_invoices_amount = serializers.FloatField()
    total_paid_amount = serializers.FloatField()
    outstanding_amount = serializers.FloatField()
    total_employees = serializers.IntegerField()
    open_issues = serializers.IntegerField()
    overdue_tasks = serializers.IntegerField()
    pending_timesheets = serializers.IntegerField()


class RevenueByClientSerializer(serializers.Serializer):
    client_name = serializers.CharField()
    total_invoiced = serializers.FloatField()
    total_paid = serializers.FloatField()
    outstanding = serializers.FloatField()


class ProjectHealthSerializer(serializers.Serializer):
    project_name = serializers.CharField()
    project_code = serializers.CharField()
    client_name = serializers.CharField()
    health = serializers.CharField()
    status = serializers.CharField()
    completion = serializers.FloatField()
    project_manager = serializers.CharField()


class ResourceUtilizationSerializer(serializers.Serializer):
    employee_name = serializers.CharField()
    total_allocated_hours = serializers.FloatField()
    total_logged_hours = serializers.FloatField()
    utilization_percentage = serializers.FloatField()
    project_count = serializers.IntegerField()


class TaskOverdueSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    project_name = serializers.CharField()
    assigned_to = serializers.CharField()
    due_date = serializers.DateField()
    status = serializers.CharField()
    days_overdue = serializers.IntegerField()
