from django.contrib import admin
from .models import (
    Attendance, LeavePolicy, LeaveBalance, LeaveRequest, WFHRequest,
    Timesheet, TimesheetEntry, ExpenseCategory, Expense
)


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'status', 'check_in', 'check_out', 'total_hours']
    list_filter = ['status', 'date']
    search_fields = ['employee__email', 'employee__first_name', 'employee__last_name']
    date_hierarchy = 'date'


@admin.register(LeavePolicy)
class LeavePolicyAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'leave_type', 'frequency', 'max_days', 'is_paid', 'is_active']
    list_filter = ['leave_type', 'frequency', 'is_paid', 'is_active']


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'leave_policy', 'year', 'total_days', 'consumed_days', 'remaining_days']
    list_filter = ['year']
    search_fields = ['employee__email', 'employee__first_name']


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ['employee', 'leave_policy', 'start_date', 'end_date', 'total_days', 'status']
    list_filter = ['status', 'leave_policy']
    search_fields = ['employee__email', 'employee__first_name']
    date_hierarchy = 'start_date'


@admin.register(WFHRequest)
class WFHRequestAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'status', 'approved_by', 'created_at']
    list_filter = ['status']
    search_fields = ['employee__email']
    date_hierarchy = 'date'


class TimesheetEntryInline(admin.TabularInline):
    model = TimesheetEntry
    extra = 1


@admin.register(Timesheet)
class TimesheetAdmin(admin.ModelAdmin):
    list_display = ['employee', 'week_start_date', 'week_end_date', 'total_hours', 'billable_hours', 'status']
    list_filter = ['status']
    search_fields = ['employee__email', 'employee__first_name']
    inlines = [TimesheetEntryInline]


@admin.register(TimesheetEntry)
class TimesheetEntryAdmin(admin.ModelAdmin):
    list_display = ['timesheet', 'date', 'project', 'task', 'hours', 'is_billable']
    list_filter = ['is_billable', 'date']
    search_fields = ['timesheet__employee__email']


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'is_active']
    search_fields = ['name']


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['employee', 'category', 'amount', 'date', 'status', 'project']
    list_filter = ['status', 'category']
    search_fields = ['employee__email', 'description']
    date_hierarchy = 'date'
