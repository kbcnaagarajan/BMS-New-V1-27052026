from rest_framework import serializers
from .models import (
    Attendance, LeavePolicy, LeaveBalance, LeaveRequest, WFHRequest,
    Timesheet, TimesheetEntry, ExpenseCategory, Expense
)


class AttendanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()

    class Meta:
        model = Attendance
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def get_employee_name(self, obj):
        return obj.employee.full_name


class LeavePolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = LeavePolicy
        fields = '__all__'


class LeaveBalanceSerializer(serializers.ModelSerializer):
    leave_policy_name = serializers.CharField(source='leave_policy.name', read_only=True)

    class Meta:
        model = LeaveBalance
        fields = '__all__'


class LeaveRequestSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    leave_type_name = serializers.CharField(source='leave_policy.name', read_only=True)

    class Meta:
        model = LeaveRequest
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def get_employee_name(self, obj):
        return obj.employee.full_name


class WFHRequestSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()

    class Meta:
        model = WFHRequest
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def get_employee_name(self, obj):
        return obj.employee.full_name


class TimesheetEntrySerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.project_name', read_only=True)
    task_title = serializers.CharField(source='task.title', read_only=True)

    class Meta:
        model = TimesheetEntry
        fields = '__all__'


class TimesheetSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    entries = TimesheetEntrySerializer(many=True, read_only=True)

    class Meta:
        model = Timesheet
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def get_employee_name(self, obj):
        return obj.employee.full_name


class TimesheetSubmissionSerializer(serializers.Serializer):
    entries = TimesheetEntrySerializer(many=True)
    notes = serializers.CharField(required=False)


class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = '__all__'


class ExpenseSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Expense
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def get_employee_name(self, obj):
        return obj.employee.full_name
