from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('user_type', 'super_admin')
        return self.create_user(email, password, **extra_fields)

    def get_for_company(self, company):
        return self.filter(company=company)


class Company(models.Model):
    COMPANY_TYPES = (
        ('enterprise', 'Enterprise'),
        ('startup', 'Startup'),
        ('agency', 'Agency'),
        ('freelancer', 'Freelancer'),
        ('other', 'Other'),
    )
    SUBSCRIPTION_STATUS = (
        ('trial', 'Trial'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
        ('cancelled', 'Cancelled'),
    )

    name = models.CharField(max_length=255)
    company_type = models.CharField(max_length=50, choices=COMPANY_TYPES, default='enterprise')
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    registration_number = models.CharField(max_length=100, blank=True)
    tax_number = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    currency = models.CharField(max_length=3, blank=True, default='USD')
    timezone = models.CharField(max_length=100, blank=True, default='UTC')
    working_days = models.CharField(max_length=100, blank=True, default='Mon,Tue,Wed,Thu,Fri', help_text="Comma-separated working days")
    working_hours = models.CharField(max_length=100, blank=True, default='9:00 AM - 6:00 PM', help_text="Working hours range")
    is_active = models.BooleanField(default=True)
    subscription_status = models.CharField(max_length=20, choices=SUBSCRIPTION_STATUS, default='trial')

    user_limit = models.IntegerField(default=10, help_text="Maximum number of users allowed")
    client_limit = models.IntegerField(default=50, help_text="Maximum number of clients allowed")
    project_limit = models.IntegerField(default=50, help_text="Maximum number of projects allowed")
    storage_limit_mb = models.IntegerField(default=1024, help_text="Storage limit in MB")
    storage_used_mb = models.IntegerField(default=0, help_text="Storage used in MB")

    company_admin = models.ForeignKey(
        'User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='admin_of_companies',
        help_text="Company admin who has full access to this company's data"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Companies'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def user_count(self):
        return self.users.filter(is_active=True).count()

    @property
    def client_count(self):
        from client_crm.models import Client
        return Client.objects.filter(company=self).count()

    @property
    def project_count(self):
        from project_360.models import Project
        return Project.objects.filter(client__company=self).count()

    @property
    def storage_used_display(self):
        if self.storage_used_mb < 1024:
            return f'{self.storage_used_mb} MB'
        return f'{self.storage_used_mb / 1024:.1f} GB'

    @property
    def storage_limit_display(self):
        if self.storage_limit_mb < 1024:
            return f'{self.storage_limit_mb} MB'
        return f'{self.storage_limit_mb / 1024:.1f} GB'

    @property
    def usage_percent(self):
        if self.storage_limit_mb == 0:
            return 0
        return min(100, round(self.storage_used_mb / self.storage_limit_mb * 100))


class Package(models.Model):
    BILLING_CYCLES = (
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
        ('one_time', 'One Time'),
    )

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True, help_text="Unique code e.g. 'starter', 'pro', 'enterprise'")
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLES, default='monthly')
    is_active = models.BooleanField(default=True)
    is_free = models.BooleanField(default=False, help_text="Free package has no billing")

    user_limit = models.IntegerField(default=5)
    client_limit = models.IntegerField(default=20)
    project_limit = models.IntegerField(default=20)
    storage_limit_mb = models.IntegerField(default=512)
    trial_days = models.IntegerField(default=14)

    features = models.TextField(blank=True, help_text="JSON list of feature descriptions")
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', 'name']

    def __str__(self):
        return f'{self.name} (${self.price}/{self.get_billing_cycle_display()})'


class CompanySubscription(models.Model):
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='subscription')
    package = models.ForeignKey(Package, on_delete=models.SET_NULL, null=True, related_name='subscriptions')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    auto_renew = models.BooleanField(default=True)
    paid_via = models.CharField(max_length=50, blank=True, help_text="Payment gateway or method")
    transaction_id = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f'{self.company.name} - {self.package.name if self.package else "No Package"}'


class CompanyInvite(models.Model):
    INVITE_STATUS = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    )

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='invites')
    email = models.EmailField()
    token = models.CharField(max_length=255, unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150, blank=True)
    role = models.CharField(max_length=50, default='company_admin')
    status = models.CharField(max_length=20, choices=INVITE_STATUS, default='pending')
    invited_by = models.ForeignKey(
        'User', on_delete=models.SET_NULL, null=True, related_name='sent_invites'
    )
    accepted_by = models.ForeignKey(
        'User', on_delete=models.SET_NULL, null=True, blank=True, related_name='accepted_invites'
    )
    accepted_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['company', 'email']
        ordering = ['-created_at']

    def __str__(self):
        return f'Invite: {self.email} -> {self.company.name}'


class Department(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['company', 'name']

    def __str__(self):
        return f'{self.company.name} - {self.name}'


class Designation(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='designations')
    title = models.CharField(max_length=255)
    level = models.IntegerField(default=0)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['company', 'title']

    def __str__(self):
        return self.title


# ========== RBAC CORE MODELS ==========

class Module(models.Model):
    """Represents a screen/module in the application for menu & permission control."""
    name = models.CharField(max_length=255)
    key = models.CharField(max_length=100, unique=True, help_text="Unique identifier e.g. 'projects', 'clients', 'timesheets'")
    icon = models.CharField(max_length=100, blank=True, help_text="CSS class for icon e.g. 'fas fa-project-diagram'")
    path = models.CharField(max_length=500, blank=True, help_text="Frontend route path e.g. '/projects'")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    sequence = models.IntegerField(default=0)
    is_menu_item = models.BooleanField(default=True, help_text="Show in navigation menu")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sequence', 'name']

    def __str__(self):
        return f'{self.name} ({self.key})'


class Permission(models.Model):
    """Granular permission definition tied to a module."""
    MODULE_PERMISSIONS = (
        ('view', 'View'), ('create', 'Create'),
        ('edit', 'Edit'), ('delete', 'Delete'),
        ('approve', 'Approve'), ('export', 'Export'),
        ('import', 'Import'), ('assign', 'Assign'),
        ('manage', 'Manage'),
    )

    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='permissions')
    codename = models.CharField(max_length=100, help_text="e.g. 'view_projects', 'create_tasks'")
    name = models.CharField(max_length=255)
    permission_type = models.CharField(max_length=50, choices=MODULE_PERMISSIONS)
    description = models.TextField(blank=True)

    class Meta:
        unique_together = ['module', 'codename']
        ordering = ['module', 'permission_type']

    def __str__(self):
        return f'{self.module.name} - {self.name}'


class Role(models.Model):
    """Collection of permissions assigned to users."""
    ROLE_CATEGORIES = (
        ('super_admin', 'Super Admin'),
        ('company_admin', 'Company Admin'),
        ('management', 'Management / Director'),
        ('delivery_manager', 'Delivery Manager'),
        ('project_manager', 'Project Manager'),
        ('account_manager', 'Account Manager'),
        ('employee', 'Employee'),
        ('hr_manager', 'HR / Resource Manager'),
        ('finance_user', 'Finance User'),
        ('client_admin', 'Client Admin'),
        ('client_user', 'Client User'),
    )

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='roles', null=True, blank=True)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=ROLE_CATEGORIES, blank=True)
    description = models.TextField(blank=True)
    is_system_role = models.BooleanField(default=False, help_text="System roles cannot be deleted")
    permissions = models.ManyToManyField(Permission, blank=True, related_name='roles')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class User(AbstractBaseUser, PermissionsMixin):
    USER_TYPES = (
        ('super_admin', 'Super Admin'),
        ('company_admin', 'Company Admin'),
        ('management', 'Management / Director'),
        ('delivery_manager', 'Delivery Manager'),
        ('project_manager', 'Project Manager'),
        ('account_manager', 'Account Manager'),
        ('employee', 'Employee'),
        ('hr_manager', 'HR / Resource Manager'),
        ('finance_user', 'Finance User'),
        ('client_admin', 'Client Admin'),
        ('client_user', 'Client User'),
    )

    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )

    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    designation = models.ForeignKey(Designation, on_delete=models.SET_NULL, null=True, blank=True)
    roles = models.ManyToManyField(Role, blank=True, related_name='users')

    employee_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    first_name = models.CharField(max_length=150)
    middle_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    joining_date = models.DateField(null=True, blank=True)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    address = models.TextField(blank=True)
    country = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)

    user_type = models.CharField(max_length=50, choices=USER_TYPES, default='employee')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_client_user = models.BooleanField(default=False)

    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.email})'

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()

    # ========== RBAC METHODS ==========

    def has_module_access(self, module_key):
        """Check if user has access to a module via any permission in that module."""
        if self.is_superuser:
            return module_key not in SUPER_ADMIN_RESTRICTED_MODULES
        if self.roles.filter(
            permissions__module__key=module_key,
            is_active=True
        ).exists():
            return True
        user_type_module_keys = self.USER_TYPE_MODULES.get(self.user_type)
        if user_type_module_keys == '__all__':
            return True
        if user_type_module_keys:
            return module_key in user_type_module_keys
        return False

    def has_perm_in_module(self, module_key, perm_type='view'):
        """Check if user has a specific permission type on a module."""
        if self.is_superuser:
            return module_key not in SUPER_ADMIN_RESTRICTED_MODULES
        if self.roles.filter(
            permissions__module__key=module_key,
            permissions__permission_type=perm_type,
            is_active=True
        ).exists():
            return True
        user_type_module_keys = self.USER_TYPE_MODULES.get(self.user_type)
        if user_type_module_keys == '__all__':
            return True
        if user_type_module_keys:
            return module_key in user_type_module_keys
        return False

    def get_module_permissions(self, module_key):
        """Get all permission types the user has for a module."""
        if self.is_superuser:
            if module_key in SUPER_ADMIN_RESTRICTED_MODULES:
                return []
            return ['view', 'create', 'edit', 'delete', 'approve', 'export', 'import', 'assign', 'manage']
        perms = list(self.roles.filter(
            permissions__module__key=module_key,
            is_active=True
        ).values_list('permissions__permission_type', flat=True).distinct())
        if perms:
            return perms
        user_type_module_keys = self.USER_TYPE_MODULES.get(self.user_type)
        if user_type_module_keys == '__all__' or (user_type_module_keys and module_key in user_type_module_keys):
            return ['view', 'create', 'edit', 'delete']
        return []

    USER_TYPE_MODULES = {
        'company_admin': '__all__',
        'management': ['dashboard', 'clients', 'projects', 'tasks', 'timesheets',
                        'meetings', 'documents',
                        'issues', 'risks', 'change_requests', 'support_tickets',
                        'invoices', 'payments', 'expenses',
                        'employees', 'timesheets', 'leave', 'attendance',
                        'reports'],
        'delivery_manager': ['dashboard', 'clients', 'projects', 'tasks', 'milestones',
                              'deliverables', 'meetings', 'documents', 'team',
                              'issues', 'risks', 'change_requests', 'support_tickets',
                              'employees', 'timesheets', 'leave', 'attendance',
                              'reports'],
        'project_manager': ['dashboard', 'clients', 'contacts', 'projects', 'tasks',
                             'milestones', 'deliverables', 'meetings', 'documents', 'team',
                             'timesheets', 'leave', 'attendance',
                             'issues', 'risks', 'change_requests', 'support_tickets',
                             'reports'],
        'account_manager': ['dashboard', 'clients', 'contacts', 'projects',
                             'meetings', 'documents',
                             'issues', 'support_tickets', 'change_requests',
                             'invoices', 'payments',
                             'reports'],
        'employee': ['dashboard', 'projects', 'tasks',
                      'timesheets', 'leave', 'attendance', 'expenses',
                      'meetings', 'documents'],
        'hr_manager': ['dashboard', 'employees', 'timesheets', 'leave', 'attendance',
                        'expenses', 'reports',
                        'departments', 'designations'],
        'finance_user': ['dashboard', 'clients', 'projects',
                          'invoices', 'payments', 'expenses',
                          'reports'],
        'client_admin': ['portal_dashboard', 'portal_projects'],
        'client_user': ['portal_dashboard', 'portal_projects'],
    }

    def get_accessible_modules(self):
        """Get all modules this user can access."""
        if self.is_superuser:
            return Module.objects.filter(key__in=SA_ALLOWED_MODULES, is_active=True)
        role_modules = Module.objects.filter(
            permissions__roles__users=self,
            permissions__roles__is_active=True,
            is_active=True
        ).distinct()
        if role_modules.exists():
            return role_modules.exclude(key__in=PLATFORM_MODULES)
        user_type_module_keys = self.USER_TYPE_MODULES.get(self.user_type)
        if user_type_module_keys == '__all__':
            return Module.objects.filter(is_active=True).exclude(key__in=PLATFORM_MODULES)
        if user_type_module_keys:
            return Module.objects.filter(key__in=user_type_module_keys, is_active=True)
        return Module.objects.none()

    def is_company_admin_user(self):
        """Check if user is a company admin."""
        return self.user_type == 'company_admin' or (
            self.company and self.company.company_admin == self
        )

    def get_accessible_companies(self):
        """Get companies this user can access data for."""
        if self.is_superuser:
            return Company.objects.filter(is_active=True)
        if self.company:
            return Company.objects.filter(id=self.company.id)
        return Company.objects.none()

    def can_access_company(self, company):
        """Check if user can access a specific company's data."""
        if self.is_superuser:
            return True
        return self.company == company

    def get_visible_profiles(self):
        """Get user profiles visible to this user based on role."""
        if self.is_superuser:
            return User.objects.filter(is_active=True)
        if self.is_company_admin_user():
            return User.objects.filter(company=self.company, is_active=True)
        return User.objects.filter(id=self.id)

    # ========== USER TYPE HELPERS ==========

    @property
    def is_super_admin(self):
        return self.is_superuser or self.user_type == 'super_admin'

    @property
    def is_management(self):
        return self.user_type in ('management', 'delivery_manager')

    @property
    def is_pm_or_above(self):
        return self.user_type in ('management', 'delivery_manager', 'project_manager')

    @property
    def is_project_staff(self):
        return self.user_type in ('employee', 'project_manager', 'account_manager')

    @property
    def is_project_manager(self):
        return self.user_type == 'project_manager'


class UserActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    action = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'User Activities'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email} - {self.action}'


# ── Super Admin Boundary ──

SUPER_ADMIN_RESTRICTED_MODULES = [
    'clients', 'contacts', 'projects', 'tasks', 'milestones', 'deliverables',
    'meetings', 'documents', 'team',
    'invoices', 'payments', 'expenses',
    'issues', 'risks', 'change_requests', 'support_tickets',
    'employees', 'timesheets', 'leave', 'attendance',
    'departments', 'designations', 'user_management', 'roles_permissions', 'users', 'roles',
    'company_settings',
    'portal_dashboard', 'portal_projects',
    # Aliases used in code
    'leaves',
]

SA_ALLOWED_MODULES = [
    'dashboard', 'companies', 'packages', 'subscriptions', 'reports',
]

PLATFORM_MODULES = {'companies', 'packages', 'subscriptions'}
