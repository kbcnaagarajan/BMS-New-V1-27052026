from django.db import models
from django.conf import settings


class ProjectIssue(models.Model):
    ISSUE_TYPES = (
        ('bug', 'Bug'), ('blocker', 'Blocker'),
        ('dependency', 'Dependency'), ('client_delay', 'Client Delay'),
        ('resource_issue', 'Resource Issue'), ('technical', 'Technical Issue'),
        ('scope_issue', 'Scope Issue'), ('payment_issue', 'Payment Issue'),
        ('approval_delay', 'Approval Delay'), ('other', 'Other'),
    )
    SEVERITY_CHOICES = (
        ('critical', 'Critical'), ('major', 'Major'),
        ('minor', 'Minor'), ('cosmetic', 'Cosmetic'),
    )
    STATUS_CHOICES = (
        ('open', 'Open'), ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'), ('closed', 'Closed'),
        ('reopened', 'Reopened'),
    )

    project = models.ForeignKey(
        'project_360.Project', on_delete=models.CASCADE,
        related_name='project_issues'
    )
    task = models.ForeignKey(
        'project_360.ProjectTask', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='issues'
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    issue_type = models.CharField(max_length=50, choices=ISSUE_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='major')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_issues'
    )
    raised_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='raised_issues'
    )
    raised_by_client = models.ForeignKey(
        'client_crm.ClientContact', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='raised_issues'
    )

    resolution = models.TextField(blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='resolved_issues'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    is_client_visible = models.BooleanField(default=True)
    target_resolution_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} - {self.project.project_name}'


class ProjectRisk(models.Model):
    SEVERITY_CHOICES = (
        ('critical', 'Critical'), ('high', 'High'),
        ('medium', 'Medium'), ('low', 'Low'),
    )
    PROBABILITY_CHOICES = (
        ('very_high', 'Very High - 80-100%'),
        ('high', 'High - 60-80%'),
        ('medium', 'Medium - 40-60%'),
        ('low', 'Low - 20-40%'),
        ('very_low', 'Very Low - 0-20%'),
    )
    IMPACT_CHOICES = (
        ('critical', 'Critical'), ('high', 'High'),
        ('medium', 'Medium'), ('low', 'Low'),
    )
    STATUS_CHOICES = (
        ('identified', 'Identified'), ('assessing', 'Assessing'),
        ('mitigating', 'Mitigating'), ('monitoring', 'Monitoring'),
        ('closed', 'Closed'),
    )

    project = models.ForeignKey(
        'project_360.Project', on_delete=models.CASCADE,
        related_name='project_risks'
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')
    probability = models.CharField(max_length=20, choices=PROBABILITY_CHOICES, default='medium')
    impact = models.CharField(max_length=20, choices=IMPACT_CHOICES, default='medium')

    risk_score = models.IntegerField(default=0, help_text="Calculated risk score (1-25)")
    mitigation_plan = models.TextField(blank=True)
    contingency_plan = models.TextField(blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='identified')
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='owned_risks'
    )
    identified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='identified_risks'
    )

    target_date = models.DateField(null=True, blank=True)
    closed_date = models.DateTimeField(null=True, blank=True)
    is_client_visible = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} - {self.project.project_name}'


class ChangeRequest(models.Model):
    PRIORITY_CHOICES = (
        ('low', 'Low'), ('medium', 'Medium'),
        ('high', 'High'), ('urgent', 'Urgent'),
    )
    STATUS_CHOICES = (
        ('draft', 'Draft'), ('submitted', 'Submitted'),
        ('impact_analysis', 'Impact Analysis'),
        ('management_review', 'Management Review'),
        ('client_approval', 'Client Approval Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('implemented', 'Implemented'),
    )

    project = models.ForeignKey(
        'project_360.Project', on_delete=models.CASCADE,
        related_name='change_requests'
    )
    cr_number = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    reason = models.TextField(blank=True)

    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='draft')

    impact_on_cost = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    impact_on_timeline = models.IntegerField(null=True, blank=True, help_text="Number of days added")
    impact_on_resources = models.TextField(blank=True)
    estimated_effort = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Hours")

    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='requested_changes'
    )
    requested_by_client = models.ForeignKey(
        'client_crm.ClientContact', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='requested_changes'
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='reviewed_changes'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='approved_changes'
    )
    client_approved = models.BooleanField(default=False)
    client_approved_by = models.ForeignKey(
        'client_crm.ClientContact', on_delete=models.SET_NULL,
        null=True, blank=True
    )

    approved_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    linked_tasks = models.ManyToManyField(
        'project_360.ProjectTask', blank=True, related_name='change_requests'
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='created_changes'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.cr_number} - {self.title}'


class SupportTicket(models.Model):
    PRIORITY_CHOICES = (
        ('low', 'Low'), ('medium', 'Medium'),
        ('high', 'High'), ('urgent', 'Urgent'),
    )
    STATUS_CHOICES = (
        ('open', 'Open'), ('in_progress', 'In Progress'),
        ('waiting_on_client', 'Waiting on Client'),
        ('resolved', 'Resolved'), ('closed', 'Closed'),
    )

    project = models.ForeignKey(
        'project_360.Project', on_delete=models.CASCADE,
        related_name='support_tickets'
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')

    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='submitted_tickets'
    )
    submitted_by_client = models.ForeignKey(
        'client_crm.ClientContact', on_delete=models.SET_NULL,
        null=True, blank=True
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_tickets'
    )

    resolution = models.TextField(blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='resolved_tickets'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} - {self.project.project_name}'
