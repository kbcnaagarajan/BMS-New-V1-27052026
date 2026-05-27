from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q, F
from django.utils import timezone
from django.http import HttpResponseForbidden
from user_management.models import User, Company, Module, Department, Designation, Role, Package, CompanySubscription, CompanyInvite, SUPER_ADMIN_RESTRICTED_MODULES
from user_management.rbac import build_user_menu
from client_crm.models import Client, ClientContact
from project_360.models import Project, ProjectTask, ProjectTeamMember, ProjectMilestone, ProjectDeliverable
from employee_operations.models import Timesheet, TimesheetEntry, LeaveRequest, LeaveBalance, Attendance, Expense, ExpenseCategory, LeavePolicy
from meetings_documents.models import Meeting, Document
from issues_risks.models import ProjectIssue, ProjectRisk, ChangeRequest, SupportTicket
from billing.models import Invoice, Payment

from django.http import HttpResponseForbidden


def _sa_check(user, module_key):
    """Return 403 response if super admin is blocked from this module, else None."""
    if user.is_superuser and module_key in SUPER_ADMIN_RESTRICTED_MODULES:
        return HttpResponseForbidden()
    return None

def _get_role_scope(user, module_key):
    """
    Return a Q object filter for the given module based on the user's role.
    - Super admin: sees company-level data but NOT personal/operational modules
    - Company admin & mgmt roles: company-scoped
    - Project Manager: projects they manage + related data
    - Employee: self-only for personal data, assigned projects for project data
    """
    if user.is_super_admin:
        # Super Admin monitors at platform level; does NOT access personal/operational data
        if module_key in ('timesheets', 'leave', 'leaves', 'attendance', 'expenses',
                          'meetings', 'documents', 'issues', 'risks',
                          'change_requests', 'support_tickets', 'team',
                          'tasks', 'milestones', 'deliverables',
                          'invoices', 'payments', 'contacts',
                          'clients', 'projects', 'employees',
                          'users', 'roles', 'departments', 'designations'):
            return Q(pk=None)
        return Q()

    role = user.user_type
    company = user.company

    # ── Company-level roles ───────────────────────────────────────────
    if role in ('company_admin', 'management', 'delivery_manager',
                'account_manager', 'hr_manager', 'finance_user'):
        return _company_scope_q(module_key, company)

    # ── Project Manager ──────────────────────────────────────────────
    if role == 'project_manager':
        return _pm_scope_q(module_key, user, company)

    # ── Employee / Staff ─────────────────────────────────────────────
    if role in ('employee', 'staff'):
        return _employee_scope_q(module_key, user, company)

    # Fallback
    return _company_scope_q(module_key, company)


def _company_scope_q(module_key, company):
    """Company-scoped filter for any module."""
    if not company:
        return Q(pk=None)
    paths = {
        'clients': 'company',
        'contacts': 'client__company',
        'projects': 'client__company',
        'tasks': 'project__client__company',
        'milestones': 'project__client__company',
        'deliverables': 'project__client__company',
        'meetings': 'project__client__company',
        'documents': 'project__client__company',
        'team': 'project__client__company',
        'invoices': 'client__company',
        'payments': 'invoice__client__company',
        'expenses': 'employee__company',
        'issues': 'project__client__company',
        'risks': 'project__client__company',
        'change_requests': 'project__client__company',
        'support_tickets': 'project__client__company',
        'attendance': 'employee__company',
        'timesheets': 'employee__company',
        'leaves': 'employee__company',
        'users': 'company',
        'roles': 'company',
        'settings': 'pk',
    }
    path = paths.get(module_key)
    if path == 'pk':
        return Q(pk=company.pk)
    if path:
        return Q(**{path: company})
    return Q()


def _pm_scope_q(module_key, user, company):
    """Project Manager scope: their managed projects / related data."""
    if module_key in ('projects',):
        return Q(project_manager=user)
    if module_key in ('tasks', 'milestones', 'deliverables', 'meetings',
                      'documents', 'team', 'expenses', 'issues', 'risks',
                      'change_requests', 'support_tickets'):
        return Q(project__project_manager=user)
    if module_key in ('invoices',):
        return Q(project__project_manager=user)
    if module_key in ('payments',):
        return Q(invoice__project__project_manager=user)
    if module_key in ('timesheets',):
        return Q(employee__company=company) if company else Q()
    if module_key in ('leaves', 'attendance'):
        return Q(employee__company=company) if company else Q()
    if module_key in ('users',):
        return Q(company=company) if company else Q()
    if module_key in ('roles',):
        return Q(company=company) | Q(is_system_role=True) if company else Q(is_system_role=True)
    if module_key in ('settings',):
        return Q(pk=company.pk) if company else Q(pk=None)
    if module_key in ('clients',):
        return Q(company=company) if company else Q()
    if module_key in ('contacts',):
        return Q(client__company=company) if company else Q()
    return Q()


def _employee_scope_q(module_key, user, company):
    """Employee scope: self-only or assigned projects."""
    if module_key in ('timesheets', 'leaves', 'attendance', 'expenses'):
        return Q(employee=user)
    if module_key in ('tasks',):
        return Q(assigned_to=user) | Q(project__team_members__user=user)
    if module_key in ('projects',):
        return Q(team_members__user=user, team_members__is_active=True)
    if module_key in ('milestones', 'deliverables', 'meetings', 'documents',
                      'team', 'issues', 'risks', 'change_requests', 'support_tickets'):
        return Q(project__team_members__user=user)
    if module_key in ('users',):
        return Q(pk=user.pk)
    if module_key in ('contacts', 'clients', 'invoices', 'payments',
                      'roles', 'settings'):
        return Q(pk=None)
    return Q(pk=None)
    return Q(pk=None)

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    error = None
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user:
            auth_login(request, user)
            return redirect('dashboard')
        error = 'Invalid email or password'
    return render(request, 'login.html', {'error': error})

def logout_view(request):
    auth_logout(request)
    return redirect('login')

def get_rbac_context(user):
    menu = build_user_menu(user)
    return {'rbac_menu': menu}

@login_required
def dashboard(request):
    ctx = get_rbac_context(request.user)
    company = request.user.company
    is_super = request.user.is_super_admin

    if is_super:
        companies = Company.objects.annotate(
            total_users=Count('users', filter=Q(users__is_active=True)),
            total_clients=Count('clients', distinct=True),
            total_projects=Count('clients__projects', distinct=True),
        )
        total_support = SupportTicket.objects.count()
        open_support = SupportTicket.objects.filter(status__in=['open', 'in_progress']).count()
        ctx.update({
            'is_platform': True,
            'total_companies': companies.count(),
            'active_companies': companies.filter(is_active=True).count(),
            'total_projects': sum(c.total_projects for c in companies),
            'total_clients': sum(c.total_clients for c in companies),
            'total_employees': User.objects.filter(is_active=True, is_superuser=False).count(),
            'total_support_tickets': total_support,
            'open_support_tickets': open_support,
            'companies': companies.order_by('-created_at')[:10],
            'recent_support_tickets': SupportTicket.objects.select_related('project__client__company').order_by('-created_at')[:10],
        })
    else:
        project_scope = _get_role_scope(request.user, 'projects')
        task_scope = _get_role_scope(request.user, 'tasks')
        client_scope = _get_role_scope(request.user, 'clients')
        user_scope = _get_role_scope(request.user, 'users')
        ctx.update({
            'total_projects': Project.objects.filter(project_scope).count(),
            'total_clients': Client.objects.filter(client_scope).count(),
            'total_employees': User.objects.filter(user_scope, is_active=True).count(),
            'total_tasks': ProjectTask.objects.filter(task_scope).count(),
            'projects': Project.objects.filter(project_scope).select_related('client', 'project_manager')[:10],
            'upcoming_tasks': ProjectTask.objects.filter(
                task_scope, due_date__gte=timezone.now().date(),
                status__in=['todo', 'in_progress']
            ).order_by('due_date')[:10],
        })
    return render(request, 'admin_pages/dashboard.html', ctx)

@login_required
def profile(request):
    ctx = get_rbac_context(request.user)
    ctx['user_obj'] = request.user
    # Build permission summary from user's role permissions
    perm_codenames = set(
        p.codename for role in request.user.roles.all() for p in role.permissions.all()
    )
    perm_summary = []
    for mod in Module.objects.filter(is_active=True, parent__isnull=True).exclude(key__startswith='group_').order_by('name'):
        perm_summary.append({
            'module': mod.name,
            'view': f'view_{mod.key}' in perm_codenames,
            'add': f'create_{mod.key}' in perm_codenames,
            'change': f'edit_{mod.key}' in perm_codenames,
            'delete': f'delete_{mod.key}' in perm_codenames,
        })
    ctx['permission_summary'] = perm_summary
    return render(request, 'admin_pages/profile.html', ctx)

@login_required
def company_list(request):
    ctx = get_rbac_context(request.user)
    user = request.user
    if user.is_super_admin:
        companies = Company.objects.annotate(
            total_users=Count('users', filter=Q(users__is_active=True)),
            total_clients=Count('clients', distinct=True),
            total_projects=Count('clients__projects', distinct=True),
        )
    else:
        companies = [user.company] if user.company else []
    ctx['companies'] = companies
    ctx['packages'] = Package.objects.filter(is_active=True) if user.is_super_admin else []
    return render(request, 'admin_pages/company_list.html', ctx)

@login_required
def company_create(request):
    if not request.user.is_super_admin:
        return HttpResponseForbidden('Only super admins can create companies')
    ctx = get_rbac_context(request.user)
    ctx['packages'] = Package.objects.filter(is_active=True)
    if request.method == 'POST':
        d = request.POST
        # Create company
        company = Company(
            name=d.get('name'),
            company_type=d.get('company_type', 'enterprise'),
            email=d.get('email', ''),
            phone=d.get('phone', ''),
            address=d.get('address', ''),
            country=d.get('country', ''),
            state=d.get('state', ''),
            city=d.get('city', ''),
            registration_number=d.get('registration_number', ''),
            tax_number=d.get('tax_number', ''),
            website=d.get('website', ''),
            subscription_status='trial',
            user_limit=5,
            client_limit=20,
            project_limit=20,
            storage_limit_mb=512,
        )
        company.save()

        # Assign package
        package_id = d.get('package')
        if package_id:
            try:
                pkg = Package.objects.get(pk=package_id)
                company.user_limit = pkg.user_limit
                company.client_limit = pkg.client_limit
                company.project_limit = pkg.project_limit
                company.storage_limit_mb = pkg.storage_limit_mb
                company.save()
                CompanySubscription.objects.create(
                    company=company,
                    package=pkg,
                    start_date=timezone.now().date(),
                    end_date=timezone.now().date() + timezone.timedelta(days=365) if not pkg.is_free else None,
                    is_active=True,
                )
            except Package.DoesNotExist:
                pass

        # Generate invite token for company admin
        admin_email = d.get('admin_email', '').strip()
        admin_first = d.get('admin_first_name', '')
        admin_last = d.get('admin_last_name', '')
        invite_token = None
        if admin_email and admin_first:
            from django.utils.crypto import get_random_string
            token = get_random_string(64)
            CompanyInvite.objects.create(
                company=company,
                email=admin_email,
                token=token,
                first_name=admin_first,
                last_name=admin_last,
                role='company_admin',
                invited_by=request.user,
                expires_at=timezone.now() + timezone.timedelta(days=7),
                status='pending',
            )
            invite_token = token

        return redirect('company_detail', pk=company.pk)
    return render(request, 'admin_pages/company_create.html', ctx)

@login_required
def company_detail(request, pk):
    user = request.user
    if not user.is_super_admin and user.company_id != pk:
        return HttpResponseForbidden('Access denied')
    ctx = get_rbac_context(request.user)
    company = get_object_or_404(Company.objects.annotate(
        total_users=Count('users', filter=Q(users__is_active=True)),
        total_clients=Count('clients', distinct=True),
        total_projects=Count('clients__projects', distinct=True),
    ), pk=pk)

    # Get detailed stats
    projects = Project.objects.filter(client__company=company).select_related('client', 'project_manager')
    clients_list = Client.objects.filter(company=company)
    users_list = User.objects.filter(company=company, is_active=True).select_related('department', 'designation')
    support_tickets = SupportTicket.objects.filter(project__client__company=company).order_by('-created_at')[:20]
    invoices = Invoice.objects.filter(client__company=company).order_by('-invoice_date')[:20]

    # Storage usage (approximate from document uploads)
    from meetings_documents.models import Document
    doc_count = Document.objects.filter(project__client__company=company).count()

    ctx.update({
        'company': company,
        'projects': projects,
        'clients_list': clients_list,
        'users_list': users_list,
        'support_tickets': support_tickets,
        'invoices': invoices,
        'doc_count': doc_count,
        'subscription': CompanySubscription.objects.filter(company=company).first(),
    })
    return render(request, 'admin_pages/company_detail.html', ctx)

@login_required
def company_edit(request, pk):
    if not request.user.is_super_admin:
        return HttpResponseForbidden('Only super admins can edit companies')
    ctx = get_rbac_context(request.user)
    company = get_object_or_404(Company, pk=pk)
    ctx['packages'] = Package.objects.filter(is_active=True)
    if request.method == 'POST':
        d = request.POST
        company.name = d.get('name', company.name)
        company.company_type = d.get('company_type', company.company_type)
        company.email = d.get('email', '')
        company.phone = d.get('phone', '')
        company.address = d.get('address', '')
        company.country = d.get('country', '')
        company.state = d.get('state', '')
        company.city = d.get('city', '')
        company.registration_number = d.get('registration_number', '')
        company.tax_number = d.get('tax_number', '')
        company.website = d.get('website', '')
        company.is_active = d.get('is_active') == 'on'
        company.subscription_status = d.get('subscription_status', company.subscription_status)

        # Update limits from package
        package_id = d.get('package')
        if package_id:
            try:
                pkg = Package.objects.get(pk=package_id)
                company.user_limit = pkg.user_limit
                company.client_limit = pkg.client_limit
                company.project_limit = pkg.project_limit
                company.storage_limit_mb = pkg.storage_limit_mb
                sub, _ = CompanySubscription.objects.get_or_create(company=company)
                sub.package = pkg
                sub.save()
            except Package.DoesNotExist:
                pass
        else:
            company.user_limit = int(d.get('user_limit', company.user_limit))
            company.client_limit = int(d.get('client_limit', company.client_limit))
            company.project_limit = int(d.get('project_limit', company.project_limit))
            company.storage_limit_mb = int(d.get('storage_limit_mb', company.storage_limit_mb))
        company.save()
        return redirect('company_detail', pk=company.pk)
    ctx['company'] = company
    ctx['subscription'] = CompanySubscription.objects.filter(company=company).first()
    return render(request, 'admin_pages/company_edit.html', ctx)

@login_required
def company_toggle_active(request, pk):
    if not request.user.is_super_admin:
        return HttpResponseForbidden()
    company = get_object_or_404(Company, pk=pk)
    company.is_active = not company.is_active
    company.save()
    return redirect('company_detail', pk=company.pk)

# --- Client CRM ---
@login_required
def client_list(request):
    sa_resp = _sa_check(request.user, 'clients')
    if sa_resp:
        return sa_resp
    ctx = get_rbac_context(request.user)
    scope = _get_role_scope(request.user, 'clients')
    clients = Client.objects.filter(scope).annotate(project_count=Count('projects'))
    ctx['clients'] = clients
    return render(request, 'client_crm/client_list.html', ctx)

@login_required
def client_detail(request, pk):
    sa_resp = _sa_check(request.user, 'clients')
    if sa_resp:
        return sa_resp
    ctx = get_rbac_context(request.user)
    scope = _get_role_scope(request.user, 'clients')
    client = get_object_or_404(Client.objects.filter(scope).annotate(project_count=Count('projects')), pk=pk)
    project_scope = _get_role_scope(request.user, 'projects')
    projects = client.projects.filter(project_scope).select_related('project_manager').all()
    notes = client.client_notes.select_related('created_by').all()[:10]
    ctx.update({'client': client, 'projects': projects, 'notes': notes})
    return render(request, 'client_crm/client_detail.html', ctx)

@login_required
def client_form(request, pk=None):
    sa_resp = _sa_check(request.user, 'clients')
    if sa_resp:
        return sa_resp
    ctx = get_rbac_context(request.user)
    scope = _get_role_scope(request.user, 'clients')
    if pk:
        client = get_object_or_404(Client.objects.filter(scope), pk=pk)
        ctx['edit'] = True
    else:
        client = None
    if request.method == 'POST':
        data = request.POST
        if not client:
            client = Client(company=request.user.company)
        client.name = data.get('name')
        if data.get('client_code'):
            client.client_code = data.get('client_code')
        elif not pk:
            client.client_code = f'CL-{timezone.now():%Y%m%d%H%M%S}'
        client.email = data.get('email')
        client.phone = data.get('phone')
        client.website = data.get('website', '')
        client.address_line1 = data.get('address_line1', '')
        client.tax_number = data.get('tax_number', '')
        client.status = data.get('status', 'active')
        client.client_type = data.get('client_type', 'company')
        if not client.created_by_id:
            client.created_by = request.user
        client.save()
        return redirect('client_detail', pk=client.pk)
    ctx['client'] = client
    return render(request, 'client_crm/client_form.html', ctx)

@login_required
def contact_list(request):
    ctx = get_rbac_context(request.user)
    sa_resp = _sa_check(request.user, 'contacts')
    if sa_resp:
        return sa_resp
    scope = _get_role_scope(request.user, 'contacts')
    contacts = ClientContact.objects.filter(scope).select_related('client')
    ctx['contacts'] = contacts
    return render(request, 'client_crm/contact_list.html', ctx)

# --- Project 360 ---
@login_required
def project_list(request):
    sa_resp = _sa_check(request.user, 'projects')
    if sa_resp:
        return sa_resp
    ctx = get_rbac_context(request.user)
    if request.user.is_client_user:
        return HttpResponseForbidden('Access denied')
    scope = _get_role_scope(request.user, 'projects')
    projects = Project.objects.filter(scope).select_related('client', 'project_manager').annotate(
        task_count=Count('tasks'), completed_tasks=Count('tasks', filter=Q(tasks__status='done'))
    )
    ctx['projects'] = projects
    return render(request, 'project_360/project_list.html', ctx)

@login_required
def project_detail(request, pk):
    sa_resp = _sa_check(request.user, 'projects')
    if sa_resp:
        return sa_resp
    ctx = get_rbac_context(request.user)
    scope = _get_role_scope(request.user, 'projects')
    project = get_object_or_404(Project.objects.filter(scope).select_related('client', 'project_manager'), pk=pk)
    tasks = ProjectTask.objects.filter(project=project).select_related('assigned_to')
    team = ProjectTeamMember.objects.filter(project=project).select_related('user')
    total_tasks = tasks.count()
    completed_tasks = tasks.filter(status='done').count()
    ctx.update({
        'project': project, 'tasks': tasks, 'team': team,
        'total_tasks': total_tasks, 'completed_tasks': completed_tasks,
    })
    return render(request, 'project_360/project_detail.html', ctx)

@login_required
def project_form(request, pk=None):
    sa_resp = _sa_check(request.user, 'projects')
    if sa_resp:
        return sa_resp
    ctx = get_rbac_context(request.user)
    scope = _get_role_scope(request.user, 'projects')
    if pk:
        project = get_object_or_404(Project.objects.filter(scope), pk=pk)
        ctx['edit'] = True
    else:
        project = None
    if request.method == 'POST':
        data = request.POST
        if not project:
            project = Project(client_id=data.get('client'))
        project.project_name = data.get('project_name')
        if data.get('project_code'):
            project.project_code = data.get('project_code')
        elif not pk:
            project.project_code = f'PRJ-{timezone.now():%Y%m%d%H%M%S}'
        project.client_id = data.get('client')
        project.project_manager_id = data.get('project_manager')
        project.description = data.get('description', '')
        project.start_date = data.get('start_date') or None
        project.expected_end_date = data.get('expected_end_date') or None
        project.status = data.get('status', 'draft')
        project.priority = data.get('priority', 'medium')
        project.budget = data.get('budget') or None
        project.health = data.get('health', 'green')
        if not project.created_by_id:
            project.created_by = request.user
        project.save()
        return redirect('project_detail', pk=project.pk)
    ctx['project'] = project
    clients = Client.objects.filter(company=request.user.company) if request.user.company else Client.objects.all()
    managers = User.objects.filter(is_active=True)
    ctx.update({'clients': clients, 'managers': managers})
    return render(request, 'project_360/project_form.html', ctx)

@login_required
def task_list(request):
    sa_resp = _sa_check(request.user, 'tasks')
    if sa_resp:
        return sa_resp
    ctx = get_rbac_context(request.user)
    scope = _get_role_scope(request.user, 'tasks')
    tasks = ProjectTask.objects.filter(scope).select_related('project', 'assigned_to')
    ctx['tasks'] = tasks
    project_scope = _get_role_scope(request.user, 'projects')
    ctx['projects'] = Project.objects.filter(project_scope)
    ctx['employees'] = User.objects.filter(is_active=True)
    return render(request, 'project_360/task_list.html', ctx)

@login_required
def task_form(request, pk=None):
    sa_resp = _sa_check(request.user, 'tasks')
    if sa_resp:
        return sa_resp
    ctx = get_rbac_context(request.user)
    scope = _get_role_scope(request.user, 'tasks')
    if pk:
        task = get_object_or_404(ProjectTask.objects.filter(scope), pk=pk)
        ctx['edit'] = True
    else:
        task = None
    if request.method == 'POST':
        data = request.POST
        if not task:
            task = ProjectTask(project_id=data.get('project'))
        task.title = data.get('title')
        task.description = data.get('description') or ''
        task.project_id = data.get('project')
        task.assigned_to_id = data.get('assigned_to')
        task.start_date = data.get('start_date') or None
        task.due_date = data.get('due_date') or None
        task.priority = data.get('priority', 'medium')
        task.status = data.get('status', 'todo')
        task.progress_percentage = data.get('progress', 0)
        task.save()
        return redirect('task_list')
    ctx['task'] = task
    project_scope = _get_role_scope(request.user, 'projects')
    ctx['projects'] = Project.objects.filter(project_scope)
    assignees = User.objects.filter(is_active=True)
    ctx.update({'projects': ctx['projects'], 'assignees': assignees})
    return render(request, 'project_360/task_form.html', ctx)

# --- Employee ---
@login_required
def employee_list(request):
    sa_resp = _sa_check(request.user, 'users')
    if sa_resp:
        return sa_resp
    ctx = get_rbac_context(request.user)
    scope = _get_role_scope(request.user, 'users')
    employees = User.objects.filter(scope, is_active=True).select_related('department', 'designation')
    ctx['employees'] = employees
    return render(request, 'employee_operations/employee_list.html', ctx)

@login_required
def employee_detail(request, pk):
    ctx = get_rbac_context(request.user)
    scope = _get_role_scope(request.user, 'users')
    emp = get_object_or_404(User.objects.filter(scope).select_related('department', 'designation'), pk=pk)
    tasks = ProjectTask.objects.filter(assigned_to=emp)[:10]
    timesheets = Timesheet.objects.filter(employee=emp).order_by('-week_start_date')[:10]
    leave_balances = LeaveBalance.objects.filter(employee=emp)
    ctx.update({'employee': emp, 'tasks': tasks, 'timesheets': timesheets, 'leave_balances': leave_balances})
    return render(request, 'employee_operations/employee_detail.html', ctx)

@login_required
def timesheet_list(request):
    ctx = get_rbac_context(request.user)
    if request.user.is_super_admin:
        return HttpResponseForbidden('Access denied')
    ts = Timesheet.objects.select_related('employee')
    user = request.user
    if user.is_super_admin:
        pass
    elif user.user_type == 'project_manager':
        ts = ts.filter(employee__in=User.objects.filter(company=user.company))
    elif user.user_type in ('employee', 'staff'):
        ts = ts.filter(employee=user)
    elif user.company:
        ts = ts.filter(employee__company=user.company)
    ctx['timesheets'] = ts
    company = user.company
    ctx['employees'] = User.objects.filter(company=company, is_active=True) if company else User.objects.filter(is_active=True)
    return render(request, 'employee_operations/timesheet_list.html', ctx)

@login_required
def leave_list(request):
    ctx = get_rbac_context(request.user)
    if request.user.is_super_admin:
        return HttpResponseForbidden('Access denied')
    scope = _get_role_scope(request.user, 'leaves')
    leaves = LeaveRequest.objects.filter(scope).select_related('employee', 'leave_policy')
    ctx['leaves'] = leaves
    company = request.user.company
    ctx['employees'] = User.objects.filter(company=company, is_active=True) if company else User.objects.filter(is_active=True)
    return render(request, 'employee_operations/leave_list.html', ctx)

# --- Client Portal ---
@login_required
def portal_dashboard(request):
    ctx = get_rbac_context(request.user)
    if request.user.is_client_user:
        client = Client.objects.filter(company=request.user.company).first()
        if client:
            project_scope = _get_role_scope(request.user, 'projects')
            projects = Project.objects.filter(project_scope, client=client)
            invoices = Invoice.objects.filter(client=client)
            ctx.update({
                'client': client,
                'total_projects': projects.count(),
                'total_invoices': invoices.count(),
                'projects': projects[:10],
                'invoices': invoices[:10],
            })
    return render(request, 'client_portal/portal_dashboard.html', ctx)

@login_required
def portal_projects(request):
    ctx = get_rbac_context(request.user)
    if request.user.is_client_user:
        client = Client.objects.filter(company=request.user.company).first()
        project_scope = _get_role_scope(request.user, 'projects')
        ctx['projects'] = Project.objects.filter(project_scope, client=client).select_related('project_manager') if client else []
    return render(request, 'client_portal/portal_projects.html', ctx)

# --- Generic Module CRUD System ---

from django.db.models.fields import DateField, DateTimeField, TimeField, BooleanField, TextField, DecimalField, IntegerField
from django.db.models.fields.related import ForeignKey, ManyToManyField

_MODEL_CONFIG = {
    'contacts': {
        'model': ClientContact,
        'list_fields': ['first_name', 'last_name', 'email', 'phone', 'client'],
        'form_fields': ['client', 'first_name', 'last_name', 'email', 'phone', 'mobile', 'designation', 'is_primary', 'notes'],
        'redirect': 'contact_list',
    },
    'milestones': {
        'model': ProjectMilestone,
        'list_fields': ['title', 'project', 'due_date', 'status'],
        'form_fields': ['project', 'title', 'description', 'start_date', 'due_date', 'status', 'progress', 'amount', 'remarks'],
        'redirect': 'milestones_list',
    },
    'deliverables': {
        'model': ProjectDeliverable,
        'list_fields': ['title', 'project', 'due_date', 'status'],
        'form_fields': ['project', 'milestone', 'title', 'description', 'assigned_to', 'due_date', 'status', 'version', 'feedback'],
        'redirect': 'deliverables_list',
    },
    'meetings': {
        'model': Meeting,
        'list_fields': ['title', 'project', 'meeting_date', 'status'],
        'form_fields': ['project', 'title', 'meeting_type', 'meeting_date', 'start_time', 'end_time', 'location', 'meeting_link', 'agenda', 'status', 'is_client_visible'],
        'redirect': 'meetings_list',
    },
    'documents': {
        'model': Document,
        'list_fields': ['title', 'project', 'document_type', 'version'],
        'form_fields': ['project', 'client', 'title', 'document_type', 'description', 'version', 'visibility'],
        'redirect': 'documents_list',
    },
    'invoices': {
        'model': Invoice,
        'list_fields': ['invoice_number', 'client', 'total_amount', 'status'],
        'form_fields': ['project', 'client', 'invoice_date', 'due_date', 'amount', 'tax_amount', 'currency', 'status', 'notes'],
        'redirect': 'invoices_list',
    },
    'payments': {
        'model': Payment,
        'list_fields': ['invoice', 'amount', 'payment_date'],
        'form_fields': ['invoice', 'project', 'client', 'amount', 'payment_date', 'payment_mode', 'reference_number', 'notes'],
        'redirect': 'payments_list',
    },
    'expenses': {
        'model': Expense,
        'list_fields': ['employee', 'category', 'amount', 'status'],
        'form_fields': ['employee', 'project', 'category', 'date', 'amount', 'description', 'payment_mode', 'is_billable', 'notes'],
        'redirect': 'expenses_list',
    },
    'issues': {
        'model': ProjectIssue,
        'list_fields': ['title', 'project', 'severity', 'status'],
        'form_fields': ['project', 'title', 'description', 'issue_type', 'severity', 'assigned_to', 'target_resolution_date', 'is_client_visible'],
        'redirect': 'issues_list',
    },
    'risks': {
        'model': ProjectRisk,
        'list_fields': ['title', 'project', 'severity', 'status'],
        'form_fields': ['project', 'title', 'description', 'severity', 'probability', 'impact', 'mitigation_plan', 'contingency_plan', 'owner', 'target_date', 'is_client_visible'],
        'redirect': 'risks_list',
    },
    'change_requests': {
        'model': ChangeRequest,
        'list_fields': ['title', 'project', 'priority', 'status'],
        'form_fields': ['project', 'title', 'description', 'reason', 'priority', 'impact_on_cost', 'impact_on_timeline', 'estimated_effort', 'client_approved'],
        'redirect': 'change_requests_list',
    },
    'support_tickets': {
        'model': SupportTicket,
        'list_fields': ['title', 'project', 'priority', 'status'],
        'form_fields': ['project', 'title', 'description', 'priority', 'assigned_to', 'submitted_by_client'],
        'redirect': 'support_tickets_list',
    },
    'attendance': {
        'model': Attendance,
        'list_fields': ['employee', 'date', 'status'],
        'form_fields': ['employee', 'date', 'check_in', 'check_out', 'status', 'total_hours', 'overtime_hours', 'location', 'notes'],
        'redirect': 'attendance_list',
    },
    'team': {
        'model': ProjectTeamMember,
        'list_fields': ['user', 'project', 'role', 'is_active'],
        'form_fields': ['project', 'user', 'role', 'is_active', 'is_billable', 'allocation_percentage', 'allocated_hours', 'start_date', 'end_date', 'notes'],
        'redirect': 'team_list',
    },
    'users': {
        'model': User,
        'list_fields': ['full_name', 'email', 'is_active'],
        'form_fields': ['email', 'first_name', 'last_name', 'user_type', 'department', 'designation', 'phone', 'password', 'is_active', 'roles'],
        'redirect': 'users_list',
    },
    'roles': {
        'model': Role,
        'list_fields': ['name', 'company', 'is_active'],
        'form_fields': ['name', 'company', 'description', 'is_active'],
        'redirect': 'roles_list',
    },
    'departments': {
        'model': Department,
        'list_fields': ['name', 'code', 'is_active'],
        'form_fields': ['name', 'code', 'description', 'is_active'],
        'redirect': 'departments_list',
    },
    'designations': {
        'model': Designation,
        'list_fields': ['title', 'level', 'is_active'],
        'form_fields': ['title', 'level', 'description', 'is_active'],
        'redirect': 'designations_list',
    },
    'settings': {
        'model': Company,
        'list_fields': ['name', 'email', 'phone', 'is_active'],
        'form_fields': ['name', 'company_type', 'email', 'phone', 'address', 'country', 'state', 'city', 'currency', 'timezone', 'working_days', 'working_hours', 'website', 'registration_number', 'tax_number'],
        'redirect': 'settings_list',
    },
    'timesheets': {
        'model': Timesheet,
        'list_fields': ['employee', 'week_start_date', 'total_hours', 'status'],
        'form_fields': ['employee', 'week_start_date', 'week_end_date', 'notes'],
        'redirect': 'timesheets_list',
    },
    'leaves': {
        'model': LeaveRequest,
        'list_fields': ['employee', 'leave_policy', 'start_date', 'status'],
        'form_fields': ['employee', 'leave_policy', 'start_date', 'end_date', 'total_days', 'reason', 'handover_to'],
        'redirect': 'leaves_list',
    },
}

_FIELD_MAP = {k: (v['model'], v['list_fields']) for k, v in _MODEL_CONFIG.items()}


def _build_fields_meta(model, fields, obj=None):
    """Build field metadata for the generic form template with current values."""
    meta = []
    for fn in fields:
        try:
            f = model._meta.get_field(fn)
            is_m2m = isinstance(f, ManyToManyField)
            is_fk = isinstance(f, ForeignKey) and not is_m2m
            is_choice = bool(f.choices) if hasattr(f, 'choices') else False
            is_date = isinstance(f, DateField)
            is_datetime = isinstance(f, DateTimeField)
            is_time = isinstance(f, TimeField)
            is_bool = isinstance(f, BooleanField)
            is_text = isinstance(f, TextField)
            is_number = isinstance(f, (IntegerField, DecimalField))
            required = not f.null and not f.blank and not is_bool and not is_m2m
            # Pre-compute current value
            val = None
            if obj:
                raw = getattr(obj, fn)
                if callable(raw): raw = raw()
                val = raw
            meta.append({
                'name': fn,
                'label': f.verbose_name.title(),
                'is_fk': is_fk,
                'is_m2m': is_m2m,
                'is_choice': is_choice,
                'is_date': is_date,
                'is_datetime': is_datetime,
                'is_time': is_time,
                'is_bool': is_bool,
                'is_text': is_text,
                'is_number': is_number,
                'required': required,
                'choices': f.choices if is_choice else None,
                'related_model': f.remote_field.model.__name__ if (is_fk or is_m2m) else None,
                'value': val,
                'value_id': getattr(obj, f'{fn}_id', None) if obj and is_fk else None,
                'value_ids': list(val.values_list('pk', flat=True)) if obj and is_m2m and val else [],
                'value_str': str(val) if val is not None else '',
            })
        except:
            meta.append({'name': fn, 'label': fn.replace('_', ' ').title(), 'is_fk': False, 'is_m2m': False, 'is_choice': False, 'is_date': False, 'is_datetime': False, 'is_time': False, 'is_bool': False, 'is_text': False, 'is_number': False, 'required': False, 'choices': None, 'related_model': None, 'value': None, 'value_id': None, 'value_ids': [], 'value_str': ''})
    return meta


def _get_company_fk_queryset(request, model_name):
    """Get a queryset for FK dropdown scoped to the user's company."""
    user = request.user
    company = user.company
    if model_name == 'Client':
        qs = Client.objects.all() if user.is_super_admin else Client.objects.filter(company=company)
    elif model_name == 'Project':
        qs = Project.objects.all() if user.is_super_admin else Project.objects.filter(client__company=company)
    elif model_name == 'ProjectMilestone':
        qs = ProjectMilestone.objects.all() if user.is_super_admin else ProjectMilestone.objects.filter(project__client__company=company)
    elif model_name == 'User':
        qs = User.objects.filter(is_active=True)
        if not user.is_super_admin and company:
            qs = qs.filter(company=company)
    elif model_name == 'Invoice':
        qs = Invoice.objects.all() if user.is_super_admin else Invoice.objects.filter(client__company=company)
    elif model_name == 'ExpenseCategory':
        qs = ExpenseCategory.objects.all() if user.is_super_admin else ExpenseCategory.objects.filter(company=company)
    elif model_name == 'Company':
        qs = Company.objects.all() if user.is_super_admin else Company.objects.filter(pk=company.pk) if company else Company.objects.none()
    elif model_name == 'Department':
        qs = Department.objects.all() if user.is_super_admin else Department.objects.filter(company=company)
    elif model_name == 'Designation':
        qs = Designation.objects.all() if user.is_super_admin else Designation.objects.filter(company=company)
    elif model_name == 'Role':
        qs = Role.objects.all() if user.is_super_admin else Role.objects.filter(Q(company=company) | Q(is_system_role=True))
    elif model_name == 'LeavePolicy':
        qs = LeavePolicy.objects.all() if user.is_super_admin else LeavePolicy.objects.filter(company=company)
    elif model_name == 'Timesheet':
        qs = Timesheet.objects.all() if user.is_super_admin else Timesheet.objects.filter(employee__company=company) if company else Timesheet.objects.none()
    else:
        qs = type(f'_{model_name}', (), {'objects': type('_Manager', (), {'all': lambda self: [], 'filter': lambda self, **kw: []})()})().objects
        # Fallback: return empty
        model_map = {c.__name__: c for c in [Client, Project, ProjectMilestone, ProjectDeliverable, User, Invoice, Payment, Expense, ExpenseCategory, Meeting, Document, ProjectTeamMember, ProjectIssue, ProjectRisk, ChangeRequest, SupportTicket, Attendance, Timesheet, LeaveRequest, LeavePolicy, Company, Department, Designation, Role]}
        cls = model_map.get(model_name)
        if cls:
            qs = cls.objects.all()[:50]
        else:
            qs = []
    return qs


def _module_list(request, key, extra_ctx=None):
    ctx = get_rbac_context(request.user)
    if request.user.is_super_admin and key in SUPER_ADMIN_RESTRICTED_MODULES:
        return HttpResponseForbidden('Access denied')
    config = _MODEL_CONFIG.get(key)
    headers, rows = [], []
    if config:
        model = config['model']
        fields = config['list_fields']
        ctx['page_title'] = model._meta.verbose_name_plural.title()
        for fn in fields:
            try:
                f = model._meta.get_field(fn)
                headers.append(f.verbose_name.title())
            except:
                headers.append(fn.replace('_', ' ').title())
        headers.append('Actions')
        scope = _get_role_scope(request.user, key)
        qs = model.objects.filter(scope)[:100]
        for obj in qs:
            vals = []
            for fn in fields:
                try:
                    v = getattr(obj, fn)
                    if callable(v): v = v()
                    if v is None: v = '—'
                    else: v = str(v)[:80]
                except: v = '—'
                vals.append(v)
            rows.append({'vals': vals, 'pk': obj.pk})
        ctx['module_key'] = key
    else:
        ctx['page_title'] = key.replace('_', ' ').title()
    ctx.update({'headers': headers, 'rows': rows, 'module_key': key})
    if extra_ctx: ctx.update(extra_ctx)
    return render(request, 'generic_module_list.html', ctx)


def _module_form(request, key, pk=None):
    ctx = get_rbac_context(request.user)
    if request.user.is_super_admin and key in SUPER_ADMIN_RESTRICTED_MODULES:
        return HttpResponseForbidden('Access denied')
    config = _MODEL_CONFIG.get(key)
    if not config:
        return HttpResponseForbidden('Invalid module')
    model = config['model']
    form_fields = config['form_fields']
    scope = _get_role_scope(request.user, key)
    obj = get_object_or_404(model.objects.filter(scope), pk=pk) if pk else None
    ctx['edit'] = bool(pk)
    ctx['page_title'] = ('Edit ' if pk else 'New ') + model._meta.verbose_name.title()
    fields_meta = _build_fields_meta(model, form_fields, obj)
    is_self_only_role = request.user.user_type in ('employee', 'staff')
    for fm in fields_meta:
        if fm['is_fk']:
            qs = _get_company_fk_queryset(request, fm['related_model'])
            # For Employee role, restrict employee FK to self only
            if is_self_only_role and fm['name'] == 'employee':
                qs = [u for u in qs if u.pk == request.user.pk]
            fm['queryset'] = list(qs)
            # Auto-select self for employee FK
            if fm['name'] == 'employee' and is_self_only_role:
                fm['value_id'] = request.user.pk
                fm['value_str'] = str(request.user)
                fm['readonly'] = True
            else:
                fm['readonly'] = False
        elif fm['is_m2m']:
            qs = _get_company_fk_queryset(request, fm['related_model'])
            fm['queryset'] = list(qs)
            fm['readonly'] = False
        else:
            fm['readonly'] = False
    ctx['fields_meta'] = fields_meta

    company = request.user.company
    if request.method == 'POST':
        data = request.POST
        if not obj:
            obj = model()
        for fn in form_fields:
            f = model._meta.get_field(fn)
            val = data.get(fn)
            if isinstance(f, ManyToManyField):
                continue  # handled after save
            elif isinstance(f, ForeignKey):
                setattr(obj, f'{fn}_id', val or None)
            elif isinstance(f, BooleanField):
                setattr(obj, fn, fn in data)
            elif isinstance(f, (IntegerField, DecimalField)):
                setattr(obj, fn, val if val else (0 if isinstance(f, IntegerField) else 0.0))
            elif isinstance(f, (DateField, DateTimeField, TimeField)):
                setattr(obj, fn, val or None)
            else:
                setattr(obj, fn, val or '')
        # Force employee to self for self-only roles
        if is_self_only_role and hasattr(model, 'employee'):
            obj.employee = request.user
        # Set auto fields
        if not pk:
            if hasattr(model, 'company') and not getattr(obj, 'company_id', None):
                if company:
                    obj.company = company
            if hasattr(model, 'client') and not getattr(obj, 'client_id', None):
                if company:
                    obj.client = Client.objects.filter(company=company).first()
            if hasattr(model, 'created_by') and not getattr(obj, 'created_by_id', None):
                obj.created_by = request.user
            if hasattr(model, 'employee') and not getattr(obj, 'employee_id', None):
                if not is_self_only_role:
                    obj.employee = request.user
            if hasattr(model, 'submitted_by') and not getattr(obj, 'submitted_by_id', None):
                obj.submitted_by = request.user
            if hasattr(model, 'invoice_number') and not obj.invoice_number:
                obj.invoice_number = f'INV-{timezone.now():%Y%m%d%H%M%S}'
            if hasattr(model, 'cr_number') and not obj.cr_number:
                obj.cr_number = f'CR-{timezone.now():%Y%m%d%H%M%S}'
        # Handle password for User model
        if isinstance(obj, User) and 'password' in form_fields:
            pw = data.get('password', '').strip()
            if pw:
                obj.set_password(pw)
        # Auto-calculate total_days for LeaveRequest
        if isinstance(obj, LeaveRequest):
            sd_str = data.get('start_date')
            ed_str = data.get('end_date')
            if sd_str and ed_str:
                from datetime import datetime as _dt, date as _date
                try:
                    sd = _dt.strptime(str(sd_str), '%Y-%m-%d').date()
                    ed = _dt.strptime(str(ed_str), '%Y-%m-%d').date()
                    obj.total_days = (ed - sd).days + 1
                except:
                    pass
        # Auto-calculate total_amount for Invoice
        if isinstance(obj, Invoice):
            amt_val = data.get('amount', 0)
            tax_val = data.get('tax_amount', 0)
            try:
                amt = Decimal(str(amt_val or 0))
                tax = Decimal(str(tax_val or 0))
            except:
                amt = Decimal('0')
                tax = Decimal('0')
            obj.total_amount = amt + tax
            if not pk:
                obj.balance_amount = obj.total_amount
        obj.save()
        # Handle M2M fields
        for fn in form_fields:
            try:
                f = model._meta.get_field(fn)
                if isinstance(f, ManyToManyField):
                    pk_list = [int(v) for v in data.getlist(fn) if v]
                    getattr(obj, fn).set(pk_list)
            except:
                pass
        # Update Invoice totals when a Payment is created
        if isinstance(obj, Payment) and not pk:
            inv = obj.invoice
            if inv:
                pay_amt = Decimal(str(obj.amount or 0))
                inv.paid_amount = (inv.paid_amount or Decimal('0')) + pay_amt
                inv.balance_amount = (inv.total_amount or Decimal('0')) - inv.paid_amount
                if inv.balance_amount <= 0:
                    inv.status = 'paid'
                elif inv.paid_amount > 0:
                    inv.status = 'partial'
                inv.save()
        return redirect(config['redirect'])

    ctx['object'] = obj
    ctx['module_key'] = key
    ctx['company'] = company
    return render(request, 'generic_module_form.html', ctx)


def _module_detail(request, key, pk):
    ctx = get_rbac_context(request.user)
    if request.user.is_super_admin and key in SUPER_ADMIN_RESTRICTED_MODULES:
        return HttpResponseForbidden('Access denied')
    config = _MODEL_CONFIG.get(key)
    if not config:
        return HttpResponseForbidden('Invalid module')
    model = config['model']
    scope = _get_role_scope(request.user, key)
    obj = get_object_or_404(model.objects.filter(scope), pk=pk)
    ctx['object'] = obj
    ctx['page_title'] = str(obj)
    ctx['module_key'] = key
    # Build field values for the detail template
    fields = config.get('form_fields', config['list_fields'])
    values = []
    for fn in fields:
        try:
            f = model._meta.get_field(fn)
            v = getattr(obj, fn)
            if callable(v): v = v()
            if v is None: v = '—'
            values.append({'label': f.verbose_name.title(), 'value': v, 'name': fn})
        except:
            values.append({'label': fn.replace('_', ' ').title(), 'value': '—', 'name': fn})
    ctx['field_values'] = values
    ctx['can_edit'] = request.user.is_super_admin or not getattr(obj, 'company_id', None) or getattr(obj, 'company_id', None) == getattr(request.user, 'company_id', None)
    return render(request, 'generic_module_detail.html', ctx)


def _module_delete(request, key, pk):
    config = _MODEL_CONFIG.get(key)
    if not config:
        return HttpResponseForbidden('Invalid module')
    model = config['model']
    scope = _get_role_scope(request.user, key)
    obj = get_object_or_404(model.objects.filter(scope), pk=pk)
    if request.method == 'POST':
        obj.delete()
        return redirect(config['redirect'])
    ctx = get_rbac_context(request.user)
    ctx['object'] = obj
    ctx['page_title'] = f'Delete {obj}'
    ctx['module_key'] = key
    ctx['cancel_url'] = config['redirect']
    return render(request, 'generic_module_confirm_delete.html', ctx)


# --- Individual List Views ---

@login_required
def milestones_list(request):
    return _module_list(request, 'milestones')

@login_required
def deliverables_list(request):
    return _module_list(request, 'deliverables')

@login_required
def meetings_list(request):
    return _module_list(request, 'meetings')

@login_required
def documents_list(request):
    return _module_list(request, 'documents')

@login_required
def team_list(request):
    return _module_list(request, 'team')

@login_required
def invoices_list(request):
    return _module_list(request, 'invoices')

@login_required
def payments_list(request):
    return _module_list(request, 'payments')

@login_required
def expenses_list(request):
    return _module_list(request, 'expenses')

@login_required
def issues_list(request):
    return _module_list(request, 'issues')

@login_required
def risks_list(request):
    return _module_list(request, 'risks')

@login_required
def change_requests_list(request):
    return _module_list(request, 'change_requests')

@login_required
def support_tickets_list(request):
    return _module_list(request, 'support_tickets')

@login_required
def attendance_list(request):
    return _module_list(request, 'attendance')

# --- Individual Form Views (Add / Edit) ---

@login_required
def contacts_form(request, pk=None):
    return _module_form(request, 'contacts', pk)

@login_required
def milestones_form(request, pk=None):
    return _module_form(request, 'milestones', pk)

@login_required
def deliverables_form(request, pk=None):
    return _module_form(request, 'deliverables', pk)

@login_required
def meetings_form(request, pk=None):
    return _module_form(request, 'meetings', pk)

@login_required
def documents_form(request, pk=None):
    return _module_form(request, 'documents', pk)

@login_required
def invoices_form(request, pk=None):
    return _module_form(request, 'invoices', pk)

@login_required
def payments_form(request, pk=None):
    return _module_form(request, 'payments', pk)

@login_required
def expenses_form(request, pk=None):
    return _module_form(request, 'expenses', pk)

@login_required
def issues_form(request, pk=None):
    return _module_form(request, 'issues', pk)

@login_required
def risks_form(request, pk=None):
    return _module_form(request, 'risks', pk)

@login_required
def change_requests_form(request, pk=None):
    return _module_form(request, 'change_requests', pk)

@login_required
def support_tickets_form(request, pk=None):
    return _module_form(request, 'support_tickets', pk)

@login_required
def attendance_form(request, pk=None):
    return _module_form(request, 'attendance', pk)

@login_required
def timesheet_form(request, pk=None):
    return _module_form(request, 'timesheets', pk)

@login_required
def leave_form(request, pk=None):
    return _module_form(request, 'leaves', pk)

@login_required
def team_form(request, pk=None):
    return _module_form(request, 'team', pk)

# --- Individual Detail Views ---

@login_required
def timesheet_detail(request, pk):
    return _module_detail(request, 'timesheets', pk)

@login_required
def leave_detail(request, pk):
    return _module_detail(request, 'leaves', pk)

@login_required
def contacts_detail(request, pk):
    return _module_detail(request, 'contacts', pk)

@login_required
def milestones_detail(request, pk):
    return _module_detail(request, 'milestones', pk)

@login_required
def deliverables_detail(request, pk):
    return _module_detail(request, 'deliverables', pk)

@login_required
def meetings_detail(request, pk):
    return _module_detail(request, 'meetings', pk)

@login_required
def documents_detail(request, pk):
    return _module_detail(request, 'documents', pk)

@login_required
def invoices_detail(request, pk):
    return _module_detail(request, 'invoices', pk)

@login_required
def payments_detail(request, pk):
    return _module_detail(request, 'payments', pk)

@login_required
def expenses_detail(request, pk):
    return _module_detail(request, 'expenses', pk)

@login_required
def issues_detail(request, pk):
    return _module_detail(request, 'issues', pk)

@login_required
def risks_detail(request, pk):
    return _module_detail(request, 'risks', pk)

@login_required
def change_requests_detail(request, pk):
    return _module_detail(request, 'change_requests', pk)

@login_required
def support_tickets_detail(request, pk):
    return _module_detail(request, 'support_tickets', pk)

@login_required
def attendance_detail(request, pk):
    return _module_detail(request, 'attendance', pk)

@login_required
def team_detail(request, pk):
    return _module_detail(request, 'team', pk)

# --- Individual Delete Views ---

@login_required
def generic_delete(request, key, pk):
    return _module_delete(request, key, pk)

@login_required
def reports_dashboard(request):
    ctx = get_rbac_context(request.user)
    if request.user.is_client_user:
        return HttpResponseForbidden('Access denied')
    ctx['page_title'] = 'Reports & Analytics'
    ctx['headers'] = ['Metric', 'Value']
    if request.user.is_super_admin:
        data = [
            ['Total Projects', str(Project.objects.count())],
            ['Total Tasks', str(ProjectTask.objects.count())],
            ['Total Clients', str(Client.objects.count())],
            ['Invoices Total', f'${Invoice.objects.aggregate(s=Sum("total_amount"))["s"] or 0:,.2f}'],
        ]
    else:
        p_scope = _get_role_scope(request.user, 'projects')
        t_scope = _get_role_scope(request.user, 'tasks')
        c_scope = _get_role_scope(request.user, 'clients')
        i_scope = _get_role_scope(request.user, 'invoices')
        data = [
            ['Total Projects', str(Project.objects.filter(p_scope).count())],
            ['Total Tasks', str(ProjectTask.objects.filter(t_scope).count())],
            ['Total Clients', str(Client.objects.filter(c_scope).count())],
            ['Invoices Total', f'${Invoice.objects.filter(i_scope).aggregate(s=Sum("total_amount"))["s"] or 0:,.2f}'],
        ]
    ctx['rows'] = [{'vals': r, 'pk': None} for r in data]
    return render(request, 'generic_module_list.html', {'module_key': 'reports', 'is_reports': True, **ctx})

@login_required
def settings_view(request):
    return _module_list(request, 'settings')

@login_required
def settings_form(request, pk=None):
    if pk and not request.user.is_super_admin:
        company = request.user.company
        if not company or company.pk != pk:
            return HttpResponseForbidden()
    return _module_form(request, 'settings', pk)

@login_required
def users_list(request):
    return _module_list(request, 'users')

@login_required
def users_form(request, pk=None):
    return _module_form(request, 'users', pk)

@login_required
def users_detail(request, pk):
    return _module_detail(request, 'users', pk)

@login_required
def roles_list(request):
    return _module_list(request, 'roles')

@login_required
def roles_form(request, pk=None):
    return _module_form(request, 'roles', pk)

@login_required
def roles_detail(request, pk):
    return _module_detail(request, 'roles', pk)

@login_required
def departments_list(request):
    return _module_list(request, 'departments')

@login_required
def departments_form(request, pk=None):
    return _module_form(request, 'departments', pk)

@login_required
def departments_detail(request, pk):
    return _module_detail(request, 'departments', pk)

@login_required
def designations_list(request):
    return _module_list(request, 'designations')

@login_required
def designations_form(request, pk=None):
    return _module_form(request, 'designations', pk)

@login_required
def designations_detail(request, pk):
    return _module_detail(request, 'designations', pk)


# --- Invite Accept (public) ---

def company_invite_accept(request, token):
    invite = get_object_or_404(CompanyInvite, token=token, status='pending')
    if invite.expires_at < timezone.now():
        invite.status = 'expired'
        invite.save()
        return render(request, 'admin_pages/invite_expired.html', {'invite': invite})
    error = None
    if request.method == 'POST':
        d = request.POST
        password = d.get('password')
        confirm = d.get('confirm_password')
        if not password or len(password) < 6:
            error = 'Password must be at least 6 characters'
        elif password != confirm:
            error = 'Passwords do not match'
        else:
            user = User.objects.create_user(
                email=invite.email,
                password=password,
                first_name=invite.first_name,
                last_name=invite.last_name,
                company=invite.company,
                user_type='company_admin',
                is_active=True,
            )
            invite.company.company_admin = user
            invite.company.is_active = True
            invite.company.subscription_status = 'active'
            invite.company.save()
            invite.status = 'accepted'
            invite.accepted_by = user
            invite.accepted_at = timezone.now()
            invite.save()
            auth_login(request, user)
            return redirect('dashboard')
    return render(request, 'admin_pages/invite_accept.html', {'invite': invite, 'error': error})
