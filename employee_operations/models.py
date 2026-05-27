from django.db import models
from django.conf import settings
from django.utils import timezone


class Attendance(models.Model):
    STATUS_CHOICES = (
        ('present', 'Present'), ('absent', 'Absent'),
        ('late', 'Late'), ('half_day', 'Half Day'),
        ('wfh', 'Work From Home'), ('on_leave', 'On Leave'),
        ('holiday', 'Holiday'), ('week_off', 'Week Off'),
    )

    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='present')
    total_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    location = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    notes = models.TextField(blank=True)
    marked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='marked_attendance')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['employee', 'date']
        ordering = ['-date']

    def __str__(self):
        return f'{self.employee.full_name} - {self.date} - {self.status}'


class LeavePolicy(models.Model):
    LEAVE_TYPES = (
        ('annual', 'Annual Leave'), ('sick', 'Sick Leave'),
        ('personal', 'Personal Leave'), ('maternity', 'Maternity Leave'),
        ('paternity', 'Paternity Leave'), ('bereavement', 'Bereavement Leave'),
        ('comp_off', 'Compensatory Off'), ('unpaid', 'Unpaid Leave'),
        ('other', 'Other'),
    )
    FREQUENCIES = (
        ('yearly', 'Yearly'), ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'), ('one_time', 'One Time'),
    )

    name = models.CharField(max_length=100)
    company = models.ForeignKey('user_management.Company', on_delete=models.CASCADE, related_name='leave_policies', null=True, blank=True)
    leave_type = models.CharField(max_length=50, choices=LEAVE_TYPES)
    frequency = models.CharField(max_length=20, choices=FREQUENCIES, default='yearly')
    max_days = models.DecimalField(max_digits=5, decimal_places=2)
    is_paid = models.BooleanField(default=True)
    is_carry_forward = models.BooleanField(default=False)
    requires_approval = models.BooleanField(default=True)
    min_notice_days = models.IntegerField(default=0)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.name} ({self.max_days} days)'


class LeaveBalance(models.Model):
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='leave_balances')
    leave_policy = models.ForeignKey(LeavePolicy, on_delete=models.CASCADE)
    total_days = models.DecimalField(max_digits=6, decimal_places=2)
    consumed_days = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    remaining_days = models.DecimalField(max_digits=6, decimal_places=2)
    year = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['employee', 'leave_policy', 'year']

    def __str__(self):
        return f'{self.employee.full_name} - {self.leave_policy.name} - {self.year}'


class LeaveRequest(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'), ('submitted', 'Submitted'),
        ('approved', 'Approved'), ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    )

    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='leave_requests')
    leave_policy = models.ForeignKey(LeavePolicy, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    total_days = models.DecimalField(max_digits=5, decimal_places=2)
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='approved_leaves'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    handover_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='leave_handovers'
    )
    document = models.FileField(upload_to='leave_documents/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.employee.full_name} - {self.leave_policy.name} ({self.start_date} to {self.end_date})'


class WFHRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'), ('approved', 'Approved'),
        ('rejected', 'Rejected'), ('cancelled', 'Cancelled'),
    )

    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wfh_requests')
    date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    rejected_reason = models.TextField(blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='approved_wfh'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['employee', 'date']

    def __str__(self):
        return f'{self.employee.full_name} - WFH {self.date}'


class Timesheet(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'), ('submitted', 'Submitted'),
        ('approved', 'Approved'), ('rejected', 'Rejected'),
        ('rework', 'Rework Required'), ('locked', 'Locked'),
        ('billed', 'Billed'),
    )

    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='timesheets')
    week_start_date = models.DateField()
    week_end_date = models.DateField()
    total_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    billable_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    non_billable_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='approved_timesheets'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['employee', 'week_start_date']
        ordering = ['-week_start_date']

    def __str__(self):
        return f'{self.employee.full_name} - Week {self.week_start_date}'


class TimesheetEntry(models.Model):
    timesheet = models.ForeignKey(Timesheet, on_delete=models.CASCADE, related_name='entries')
    date = models.DateField()
    project = models.ForeignKey(
        'project_360.Project', on_delete=models.CASCADE,
        related_name='timesheet_entries'
    )
    task = models.ForeignKey(
        'project_360.ProjectTask', on_delete=models.CASCADE,
        null=True, blank=True, related_name='timesheet_entries'
    )
    milestone = models.ForeignKey(
        'project_360.ProjectMilestone', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='timesheet_entries'
    )
    hours = models.DecimalField(max_digits=5, decimal_places=2)
    description = models.TextField(blank=True)
    is_billable = models.BooleanField(default=True)
    is_overtime = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.timesheet.employee.full_name} - {self.date} - {self.project.project_name} - {self.hours}h'


class ExpenseCategory(models.Model):
    name = models.CharField(max_length=255)
    company = models.ForeignKey('user_management.Company', on_delete=models.CASCADE, related_name='expense_categories', null=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Expense Categories'

    def __str__(self):
        return self.name


class Expense(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'), ('submitted', 'Submitted'),
        ('approved', 'Approved'), ('rejected', 'Rejected'),
        ('reimbursed', 'Reimbursed'),
    )
    PAYMENT_MODES = (
        ('cash', 'Cash'), ('card', 'Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('upi', 'UPI'), ('other', 'Other'),
    )

    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='expenses')
    project = models.ForeignKey(
        'project_360.Project', on_delete=models.CASCADE,
        null=True, blank=True, related_name='expenses'
    )
    category = models.ForeignKey(ExpenseCategory, on_delete=models.SET_NULL, null=True)
    date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField()
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODES, default='cash')
    receipt = models.FileField(upload_to='expense_receipts/', blank=True, null=True)
    is_billable = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='approved_expenses'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f'{self.employee.full_name} - {self.amount} - {self.date}'
