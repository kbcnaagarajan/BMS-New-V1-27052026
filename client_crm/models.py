from django.db import models
from django.conf import settings


class Client(models.Model):
    CLIENT_TYPES = (
        ('company', 'Company'),
        ('individual', 'Individual'),
        ('government', 'Government'),
        ('non_profit', 'Non-Profit'),
    )

    INDUSTRIES = (
        ('technology', 'Technology'),
        ('finance', 'Finance'),
        ('healthcare', 'Healthcare'),
        ('education', 'Education'),
        ('manufacturing', 'Manufacturing'),
        ('retail', 'Retail'),
        ('construction', 'Construction'),
        ('consulting', 'Consulting'),
        ('other', 'Other'),
    )

    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
        ('closed', 'Closed'),
    )

    company = models.ForeignKey('user_management.Company', on_delete=models.CASCADE, related_name='clients', null=True, blank=True)
    client_code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    client_type = models.CharField(max_length=50, choices=CLIENT_TYPES, default='company')
    industry = models.CharField(max_length=100, choices=INDUSTRIES, blank=True)

    registration_number = models.CharField(max_length=100, blank=True)
    tax_number = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    phone = models.CharField(max_length=50)
    email = models.EmailField()

    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=20, blank=True)

    contract_start_date = models.DateField(null=True, blank=True)
    contract_end_date = models.DateField(null=True, blank=True)
    billing_terms = models.TextField(blank=True)
    sla_terms = models.TextField(blank=True)
    support_terms = models.TextField(blank=True)

    assigned_account_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='managed_clients'
    )
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='active')
    notes = models.TextField(blank=True)
    logo = models.ImageField(upload_to='client_logos/', blank=True, null=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_clients')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.client_code})'


class ClientContact(models.Model):
    SALUTATION_CHOICES = (
        ('mr', 'Mr.'), ('ms', 'Ms.'), ('mrs', 'Mrs.'), ('dr', 'Dr.'), ('prof', 'Prof.')
    )

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='contacts')
    salutation = models.CharField(max_length=10, choices=SALUTATION_CHOICES, blank=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150, blank=True)
    designation = models.CharField(max_length=255, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)
    mobile = models.CharField(max_length=50, blank=True)
    is_primary = models.BooleanField(default=False)
    can_login = models.BooleanField(default=False)
    portal_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='client_contacts'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['client', 'email']

    def __str__(self):
        return f'{self.first_name} {self.last_name} - {self.client.name}'


class ClientLocation(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='locations')
    location_name = models.CharField(max_length=255)
    address = models.TextField(blank=True)
    country = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=20, blank=True)
    is_headquarters = models.BooleanField(default=False)
    contact_person = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.location_name} - {self.client.name}'


class ClientContract(models.Model):
    CONTRACT_STATUS = (
        ('draft', 'Draft'), ('active', 'Active'),
        ('completed', 'Completed'), ('terminated', 'Terminated'),
    )

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='contracts')
    contract_title = models.CharField(max_length=255)
    contract_number = models.CharField(max_length=100, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, default='INR')
    document = models.FileField(upload_to='client_contracts/', blank=True, null=True)
    status = models.CharField(max_length=50, choices=CONTRACT_STATUS, default='draft')
    signed_by_client = models.BooleanField(default=False)
    signed_by_company = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.contract_title} - {self.client.name}'


class ClientNote(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='client_notes')
    note = models.TextField()
    is_client_visible = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Note for {self.client.name} - {self.created_at.date()}'


class ClientCommunicationLog(models.Model):
    COMM_TYPES = (
        ('email', 'Email'), ('call', 'Call'), ('meeting', 'Meeting'),
        ('whatsapp', 'WhatsApp'), ('portal', 'Portal Message'), ('other', 'Other'),
    )
    DIRECTIONS = (
        ('inbound', 'Inbound'), ('outbound', 'Outbound'),
    )

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='communications')
    communication_type = models.CharField(max_length=50, choices=COMM_TYPES)
    subject = models.CharField(max_length=255)
    message = models.TextField(blank=True)
    direction = models.CharField(max_length=20, choices=DIRECTIONS)
    contact_person = models.CharField(max_length=255, blank=True)
    communicated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    communicated_at = models.DateTimeField(auto_now_add=True)
    attachment = models.FileField(upload_to='client_communications/', blank=True, null=True)

    class Meta:
        ordering = ['-communicated_at']
        verbose_name = 'Client Communication Log'
        verbose_name_plural = 'Client Communication Logs'

    def __str__(self):
        return f'{self.get_communication_type_display()} - {self.subject}'


class ClientPortalInvite(models.Model):
    INVITE_STATUS = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    )

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='portal_invites')
    email = models.EmailField()
    token = models.CharField(max_length=255, unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150, blank=True)
    status = models.CharField(max_length=20, choices=INVITE_STATUS, default='pending')
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='sent_client_invites'
    )
    accepted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='accepted_client_invites'
    )
    accepted_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Client Invite: {self.email} -> {self.client.name}'
