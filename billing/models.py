from django.db import models
from django.conf import settings


class BillingMilestone(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'), ('achieved', 'Achieved'),
        ('invoiced', 'Invoiced'), ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    )

    project = models.ForeignKey(
        'project_360.Project', on_delete=models.CASCADE,
        related_name='billing_milestones'
    )
    milestone = models.OneToOneField(
        'project_360.ProjectMilestone', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='billing_milestone'
    )
    title = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.title} - {self.project.project_name} - {self.amount}'


class Invoice(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'), ('sent', 'Sent'),
        ('partial', 'Partially Paid'), ('paid', 'Paid'),
        ('overdue', 'Overdue'), ('cancelled', 'Cancelled'),
        ('write_off', 'Written Off'),
    )

    invoice_number = models.CharField(max_length=100, unique=True)
    project = models.ForeignKey(
        'project_360.Project', on_delete=models.CASCADE,
        related_name='invoices'
    )
    client = models.ForeignKey(
        'client_crm.Client', on_delete=models.CASCADE,
        related_name='invoices'
    )
    billing_milestone = models.ForeignKey(
        BillingMilestone, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='invoices'
    )

    invoice_date = models.DateField()
    due_date = models.DateField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    balance_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)

    currency = models.CharField(max_length=10, default='INR')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    notes = models.TextField(blank=True)
    invoice_document = models.FileField(upload_to='invoices/', blank=True, null=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='created_invoices'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-invoice_date']

    def __str__(self):
        return f'{self.invoice_number} - {self.client.name} - {self.total_amount}'


class Payment(models.Model):
    PAYMENT_MODES = (
        ('bank_transfer', 'Bank Transfer'), ('cheque', 'Cheque'),
        ('cash', 'Cash'), ('card', 'Card'),
        ('upi', 'UPI'), ('online', 'Online Payment'),
        ('other', 'Other'),
    )

    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE,
        related_name='payments'
    )
    project = models.ForeignKey(
        'project_360.Project', on_delete=models.CASCADE,
        related_name='payments'
    )
    client = models.ForeignKey(
        'client_crm.Client', on_delete=models.CASCADE,
        related_name='payments'
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    payment_date = models.DateField()
    payment_mode = models.CharField(max_length=50, choices=PAYMENT_MODES)
    reference_number = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    receipt_document = models.FileField(upload_to='payment_receipts/', blank=True, null=True)
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='received_payments'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-payment_date']

    def __str__(self):
        return f'Payment {self.reference_number} - {self.amount} - {self.invoice.invoice_number}'
