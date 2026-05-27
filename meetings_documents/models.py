from django.db import models
from django.conf import settings


class Meeting(models.Model):
    MEETING_TYPES = (
        ('internal', 'Internal Project Meeting'),
        ('client_review', 'Client Review Meeting'),
        ('steering', 'Steering Committee Meeting'),
        ('technical', 'Technical Discussion'),
        ('uat', 'UAT Meeting'),
        ('kickoff', 'Kickoff Meeting'),
        ('closure', 'Closure Meeting'),
        ('other', 'Other'),
    )
    STATUS_CHOICES = (
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rescheduled', 'Rescheduled'),
    )

    project = models.ForeignKey(
        'project_360.Project', on_delete=models.CASCADE,
        related_name='meetings'
    )
    title = models.CharField(max_length=255)
    meeting_type = models.CharField(max_length=50, choices=MEETING_TYPES, default='internal')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')

    meeting_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField(null=True, blank=True)
    location = models.CharField(max_length=255, blank=True)
    meeting_link = models.URLField(blank=True, help_text="Virtual meeting link")

    agenda = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    minutes = models.TextField(blank=True)
    minutes_document = models.FileField(upload_to='meeting_minutes/', blank=True, null=True)

    attendees = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name='meetings'
    )
    client_attendees = models.ManyToManyField(
        'client_crm.ClientContact', blank=True, related_name='meetings'
    )

    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='organized_meetings'
    )
    is_client_visible = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-meeting_date', '-start_time']

    def __str__(self):
        return f'{self.title} - {self.meeting_date} - {self.project.project_name}'


class MeetingActionItem(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'), ('in_progress', 'In Progress'),
        ('completed', 'Completed'), ('cancelled', 'Cancelled'),
    )

    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='action_items')
    description = models.TextField()
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='action_items'
    )
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    linked_task = models.ForeignKey(
        'project_360.ProjectTask', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='meeting_action_items'
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.description[:50]} - {self.meeting.title}'


class Document(models.Model):
    DOCUMENT_TYPES = (
        ('sow', 'SOW'), ('contract', 'Contract'),
        ('proposal', 'Proposal'), ('project_plan', 'Project Plan'),
        ('brd', 'BRD'), ('fsd', 'FSD'),
        ('technical', 'Technical Document'),
        ('meeting_minutes', 'Meeting Minutes'),
        ('uat', 'UAT Document'), ('sign_off', 'Sign-Off'),
        ('invoice', 'Invoice'), ('payment_proof', 'Payment Proof'),
        ('client_doc', 'Client Document'),
        ('internal_note', 'Internal Note'),
        ('other', 'Other'),
    )

    project = models.ForeignKey(
        'project_360.Project', on_delete=models.CASCADE,
        null=True, blank=True, related_name='project_documents'
    )
    client = models.ForeignKey(
        'client_crm.Client', on_delete=models.CASCADE,
        null=True, blank=True, related_name='client_documents'
    )
    title = models.CharField(max_length=255)
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES, default='other')
    description = models.TextField(blank=True)
    document = models.FileField(upload_to='documents/', null=True, blank=True)
    version = models.CharField(max_length=20, blank=True)

    visibility = models.CharField(max_length=20, choices=(
        ('internal', 'Internal Only'),
        ('client_visible', 'Client Visible'),
        ('management', 'Management Only'),
        ('team', 'Project Team Only'),
    ), default='internal')

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='uploaded_docs'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} - {self.get_document_type_display()}'


class Notification(models.Model):
    NOTIF_TYPES = (
        ('info', 'Information'), ('success', 'Success'),
        ('warning', 'Warning'), ('error', 'Error'),
        ('approval', 'Approval Required'), ('reminder', 'Reminder'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIF_TYPES, default='info')
    link = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} - {self.user.email}'
