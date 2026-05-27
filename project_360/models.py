from django.db import models
from django.conf import settings


class Project(models.Model):
    PRIORITY_CHOICES = (
        ('low', 'Low'), ('medium', 'Medium'),
        ('high', 'High'), ('urgent', 'Urgent'),
    )
    STATUS_CHOICES = (
        ('draft', 'Draft'), ('approved', 'Approved'),
        ('kickoff_scheduled', 'Kickoff Scheduled'),
        ('active', 'Active'), ('on_hold', 'On Hold'),
        ('delayed', 'Delayed'), ('completed', 'Completed'),
        ('closed', 'Closed'), ('cancelled', 'Cancelled'),
    )
    HEALTH_CHOICES = (
        ('green', 'Green - On Track'),
        ('amber', 'Amber - Needs Attention'),
        ('red', 'Red - Critical / Delayed'),
    )
    BILLING_TYPES = (
        ('fixed', 'Fixed Price'), ('hourly', 'Hourly'),
        ('milestone', 'Milestone Based'), ('retainer', 'Retainer'),
        ('t_and_m', 'Time & Material'),
    )

    client = models.ForeignKey(
        'client_crm.Client', on_delete=models.CASCADE,
        related_name='projects'
    )
    project_name = models.CharField(max_length=255)
    project_code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    project_objectives = models.TextField(blank=True)
    scope = models.TextField(blank=True)

    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='draft')
    health = models.CharField(max_length=10, choices=HEALTH_CHOICES, default='green')

    start_date = models.DateField(null=True, blank=True)
    expected_end_date = models.DateField(null=True, blank=True)
    actual_end_date = models.DateField(null=True, blank=True)
    closure_date = models.DateField(null=True, blank=True)

    budget = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, default='INR')
    billing_type = models.CharField(max_length=20, choices=BILLING_TYPES, default='fixed')
    is_billable = models.BooleanField(default=True)
    estimated_hours = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    actual_hours = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    completion_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    project_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='managed_projects'
    )
    delivery_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='delivery_projects'
    )
    account_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='account_projects'
    )
    client_spoc = models.ForeignKey(
        'client_crm.ClientContact', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='projects'
    )

    project_type = models.CharField(max_length=100, blank=True)
    tags = models.TextField(blank=True, help_text="Comma-separated tags")

    sow_document = models.FileField(upload_to='project_sow/', blank=True, null=True)
    closure_report = models.FileField(upload_to='project_closure/', blank=True, null=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='created_projects'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.project_code} - {self.project_name}'


class ProjectTeamMember(models.Model):
    PROJECT_ROLES = (
        ('project_manager', 'Project Manager'),
        ('delivery_manager', 'Delivery Manager'),
        ('account_manager', 'Account Manager'),
        ('business_analyst', 'Business Analyst'),
        ('backend_dev', 'Backend Developer'),
        ('frontend_dev', 'Frontend Developer'),
        ('fullstack_dev', 'Full Stack Developer'),
        ('integration_engineer', 'Integration Engineer'),
        ('qa_tester', 'QA Tester'),
        ('ui_designer', 'UI Designer'),
        ('devops_engineer', 'DevOps Engineer'),
        ('support_engineer', 'Support Engineer'),
        ('data_analyst', 'Data Analyst'),
        ('consultant', 'Consultant'),
        ('other', 'Other'),
    )

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='team_members')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='project_assignments')
    role = models.CharField(max_length=50, choices=PROJECT_ROLES)
    is_active = models.BooleanField(default=True)
    is_client_visible = models.BooleanField(default=True)
    is_billable = models.BooleanField(default=True)
    allocation_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=100.00)
    allocated_hours = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    joined_date = models.DateField(null=True, blank=True)
    exited_date = models.DateField(null=True, blank=True)
    reporting_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='team_members'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['project', 'user', 'role']

    def __str__(self):
        return f'{self.user.full_name} - {self.get_role_display()} - {self.project.project_name}'


class ProjectMilestone(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'), ('in_progress', 'In Progress'),
        ('completed', 'Completed'), ('delayed', 'Delayed'),
        ('cancelled', 'Cancelled'),
    )

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='milestones')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    start_date = models.DateField(null=True, blank=True)
    due_date = models.DateField()
    completion_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    progress = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    is_invoiced = models.BooleanField(default=False)
    client_approval_required = models.BooleanField(default=False)
    client_approved = models.BooleanField(default=False)
    remarks = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='created_milestones'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['due_date']

    def __str__(self):
        return f'{self.title} - {self.project.project_name}'


class ProjectTask(models.Model):
    PRIORITY_CHOICES = (
        ('low', 'Low'), ('medium', 'Medium'),
        ('high', 'High'), ('urgent', 'Urgent'),
    )
    STATUS_CHOICES = (
        ('new', 'New'), ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'), ('blocked', 'Blocked'),
        ('internal_review', 'Internal Review'),
        ('client_review', 'Client Review'),
        ('rework_required', 'Rework Required'),
        ('completed', 'Completed'), ('closed', 'Closed'),
    )
    TASK_TYPES = (
        ('development', 'Development'), ('design', 'Design'),
        ('testing', 'Testing'), ('documentation', 'Documentation'),
        ('meeting', 'Meeting'), ('research', 'Research'),
        ('support', 'Support'), ('other', 'Other'),
    )

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    milestone = models.ForeignKey(
        ProjectMilestone, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='tasks'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    task_type = models.CharField(max_length=50, choices=TASK_TYPES, default='development')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='new')

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_tasks'
    )
    start_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    completed_date = models.DateTimeField(null=True, blank=True)

    estimated_hours = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    actual_hours = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    depends_on = models.ForeignKey(
        'self', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='dependent_tasks'
    )
    is_client_visible = models.BooleanField(default=True)
    requires_client_approval = models.BooleanField(default=False)
    client_approved = models.BooleanField(default=False)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='created_tasks'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} - {self.project.project_name}'


class TaskComment(models.Model):
    task = models.ForeignKey(ProjectTask, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    comment = models.TextField()
    is_client_visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Comment by {self.user.full_name} on {self.task.title}'


class TaskAttachment(models.Model):
    task = models.ForeignKey(ProjectTask, on_delete=models.CASCADE, related_name='attachments')
    title = models.CharField(max_length=255, blank=True)
    document = models.FileField(upload_to='task_attachments/')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or f'Attachment for {self.task.title}'


class ProjectDeliverable(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'), ('submitted', 'Submitted'),
        ('pm_review', 'PM Review'), ('client_review', 'Client Review'),
        ('rework', 'Rework Required'), ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='deliverables')
    milestone = models.ForeignKey(
        ProjectMilestone, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='deliverables'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_deliverables'
    )
    due_date = models.DateField(null=True, blank=True)
    submitted_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    document = models.FileField(upload_to='deliverables/', blank=True, null=True)
    version = models.CharField(max_length=20, blank=True)
    feedback = models.TextField(blank=True)
    client_approved = models.BooleanField(default=False)
    approved_by_client_at = models.DateTimeField(null=True, blank=True)

    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='submitted_deliverables'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='created_deliverables'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.title} - {self.project.project_name}'


class ProjectStatusUpdate(models.Model):
    HEALTH_CHOICES = (
        ('green', 'Green - On Track'),
        ('amber', 'Amber - Needs Attention'),
        ('red', 'Red - Critical / Delayed'),
    )

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='status_updates')
    health = models.CharField(max_length=10, choices=HEALTH_CHOICES, default='green')

    week_start_date = models.DateField(null=True, blank=True)
    week_end_date = models.DateField(null=True, blank=True)

    progress_summary = models.TextField(blank=True)
    accomplishments = models.TextField(blank=True, help_text="What was completed this period")
    ongoing_work = models.TextField(blank=True, help_text="What is currently being worked on")
    next_steps = models.TextField(blank=True, help_text="Planned work for next period")
    blockers = models.TextField(blank=True)
    risks = models.TextField(blank=True)
    issues = models.TextField(blank=True)
    client_dependencies = models.TextField(blank=True)
    required_approvals = models.TextField(blank=True)

    budget_impact = models.TextField(blank=True)
    timeline_impact = models.TextField(blank=True)

    completion_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    is_client_visible = models.BooleanField(default=True)
    is_published = models.BooleanField(default=False)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='project_status_updates'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Project Status Updates'

    def __str__(self):
        return f'Status Update - {self.project.project_name} ({self.created_at.date()})'


class ProjectDocument(models.Model):
    DOCUMENT_TYPES = (
        ('sow', 'SOW'), ('contract', 'Contract'), ('proposal', 'Proposal'),
        ('project_plan', 'Project Plan'), ('brd', 'BRD'), ('fsd', 'FSD'),
        ('technical', 'Technical Document'), ('meeting_minutes', 'Meeting Minutes'),
        ('uat_document', 'UAT Document'), ('sign_off', 'Sign-Off'),
        ('invoice', 'Invoice'), ('payment_proof', 'Payment Proof'),
        ('client_document', 'Client Document'), ('internal_notes', 'Internal Notes'),
        ('other', 'Other'),
    )

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=255)
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES, default='other')
    description = models.TextField(blank=True)
    document = models.FileField(upload_to='project_documents/')
    version = models.CharField(max_length=20, blank=True)

    is_client_visible = models.BooleanField(default=False)
    is_management_only = models.BooleanField(default=False)

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='uploaded_documents'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} - {self.project.project_name}'


class ProjectActivityLog(models.Model):
    ACTION_TYPES = (
        ('created', 'Created'), ('updated', 'Updated'),
        ('status_change', 'Status Change'), ('comment', 'Comment'),
        ('assignment', 'Assignment'), ('approval', 'Approval'),
        ('rejection', 'Rejection'), ('upload', 'Upload'),
        ('other', 'Other'),
    )

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='activity_logs')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES, default='other')
    description = models.TextField()
    is_client_visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Project Activity Logs'

    def __str__(self):
        return f'{self.action_type} - {self.project.project_name} by {self.user.full_name if self.user else "System"}'


class ProjectClosureChecklist(models.Model):
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='closure_checklist')

    all_tasks_completed = models.BooleanField(default=False)
    all_milestones_closed = models.BooleanField(default=False)
    all_deliverables_approved = models.BooleanField(default=False)
    final_documents_uploaded = models.BooleanField(default=False)
    pending_invoices_checked = models.BooleanField(default=False)
    client_signoff_obtained = models.BooleanField(default=False)
    closure_report_submitted = models.BooleanField(default=False)

    lessons_learned = models.TextField(blank=True)
    client_feedback = models.TextField(blank=True)

    is_closed = models.BooleanField(default=False)
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='closed_projects'
    )
    closed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Closure Checklist - {self.project.project_name}'
