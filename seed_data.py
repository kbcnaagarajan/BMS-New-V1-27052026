"""
Seed script for RBAC system - creates default modules, permissions, and system roles.
Run with: python seed_data.py
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'KarthikAi_OMS.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from user_management.models import Module, Permission, Role, User
from employee_operations.models import LeavePolicy, ExpenseCategory
from user_management.models import Company


def seed_modules():
    # Group header modules (parent=None, path='', act as section headers)
    groups = [
        {'name': 'CLIENTS & CONTACTS', 'key': 'group_client', 'icon': '', 'path': '', 'sequence': 10},
        {'name': 'PROJECTS & TASKS', 'key': 'group_project', 'icon': '', 'path': '', 'sequence': 20},
        {'name': 'COLLABORATION', 'key': 'group_collab', 'icon': '', 'path': '', 'sequence': 30},
        {'name': 'FINANCE', 'key': 'group_finance', 'icon': '', 'path': '', 'sequence': 40},
        {'name': 'ISSUES & RISKS', 'key': 'group_issues', 'icon': '', 'path': '', 'sequence': 50},
        {'name': 'PEOPLE', 'key': 'group_people', 'icon': '', 'path': '', 'sequence': 60},
        {'name': 'REPORTS & ANALYTICS', 'key': 'group_reports', 'icon': '', 'path': '', 'sequence': 70},
        {'name': 'ADMINISTRATION', 'key': 'group_admin', 'icon': '', 'path': '', 'sequence': 80},
        {'name': 'CLIENT PORTAL', 'key': 'group_portal', 'icon': '', 'path': '', 'sequence': 90},
        {'name': 'PLATFORM', 'key': 'group_platform', 'icon': '', 'path': '', 'sequence': 5},
    ]

    created = []
    for g in groups:
        mod, is_new = Module.objects.get_or_create(key=g['key'], defaults=g)
        if is_new:
            created.append(mod.name)
    print(f'Groups: {len(groups)} total, {len(created)} new created')

    # Menu items (children of groups or standalone)
    modules_data = [
        # Standalone (parent=None)
        {'name': 'Dashboard', 'key': 'dashboard', 'icon': 'bi bi-speedometer2', 'path': '/dashboard/', 'parent': None, 'sequence': 1},
        # CLIENTS & CONTACTS
        {'name': 'Clients', 'key': 'clients', 'icon': 'bi bi-building', 'path': '/clients/', 'parent': 'group_client', 'sequence': 11},
        {'name': 'Contacts', 'key': 'contacts', 'icon': 'bi bi-person-lines-fill', 'path': '/contacts/', 'parent': 'group_client', 'sequence': 12},
        # PROJECTS & TASKS
        {'name': 'Projects', 'key': 'projects', 'icon': 'bi bi-kanban', 'path': '/projects/', 'parent': 'group_project', 'sequence': 21},
        {'name': 'Tasks', 'key': 'tasks', 'icon': 'bi bi-check2-square', 'path': '/tasks/', 'parent': 'group_project', 'sequence': 22},
        {'name': 'Milestones', 'key': 'milestones', 'icon': 'bi bi-flag', 'path': '/milestones/', 'parent': 'group_project', 'sequence': 23},
        {'name': 'Deliverables', 'key': 'deliverables', 'icon': 'bi bi-file-earmark-arrow-up', 'path': '/deliverables/', 'parent': 'group_project', 'sequence': 24},
        # COLLABORATION
        {'name': 'Meetings', 'key': 'meetings', 'icon': 'bi bi-calendar-event', 'path': '/meetings/', 'parent': 'group_collab', 'sequence': 31},
        {'name': 'Documents', 'key': 'documents', 'icon': 'bi bi-folder', 'path': '/documents/', 'parent': 'group_collab', 'sequence': 32},
        {'name': 'Team', 'key': 'team', 'icon': 'bi bi-people', 'path': '/team/', 'parent': 'group_collab', 'sequence': 33},
        # FINANCE
        {'name': 'Invoices', 'key': 'invoices', 'icon': 'bi bi-receipt', 'path': '/invoices/', 'parent': 'group_finance', 'sequence': 41},
        {'name': 'Payments', 'key': 'payments', 'icon': 'bi bi-credit-card', 'path': '/payments/', 'parent': 'group_finance', 'sequence': 42},
        {'name': 'Expenses', 'key': 'expenses', 'icon': 'bi bi-cash-stack', 'path': '/expenses/', 'parent': 'group_finance', 'sequence': 43},
        # ISSUES & RISKS
        {'name': 'Issues', 'key': 'issues', 'icon': 'bi bi-exclamation-triangle', 'path': '/issues/', 'parent': 'group_issues', 'sequence': 51},
        {'name': 'Risks', 'key': 'risks', 'icon': 'bi bi-shield-exclamation', 'path': '/risks/', 'parent': 'group_issues', 'sequence': 52},
        {'name': 'Change Requests', 'key': 'change_requests', 'icon': 'bi bi-arrow-left-right', 'path': '/change-requests/', 'parent': 'group_issues', 'sequence': 53},
        {'name': 'Support Tickets', 'key': 'support_tickets', 'icon': 'bi bi-ticket', 'path': '/support-tickets/', 'parent': 'group_issues', 'sequence': 54},
        # PEOPLE
        {'name': 'Employees', 'key': 'employees', 'icon': 'bi bi-person-badge', 'path': '/employees/', 'parent': 'group_people', 'sequence': 61},
        {'name': 'Timesheets', 'key': 'timesheets', 'icon': 'bi bi-clock', 'path': '/timesheets/', 'parent': 'group_people', 'sequence': 62},
        {'name': 'Leave', 'key': 'leave', 'icon': 'bi bi-calendar-minus', 'path': '/leaves/', 'parent': 'group_people', 'sequence': 63},
        {'name': 'Attendance', 'key': 'attendance', 'icon': 'bi bi-calendar-check', 'path': '/attendance/', 'parent': 'group_people', 'sequence': 64},
        # REPORTS & ANALYTICS
        {'name': 'Reports', 'key': 'reports', 'icon': 'bi bi-bar-chart-line', 'path': '/reports/', 'parent': 'group_reports', 'sequence': 71},
        # ADMINISTRATION
        {'name': 'Company Settings', 'key': 'company_settings', 'icon': 'bi bi-gear', 'path': '/settings/', 'parent': 'group_admin', 'sequence': 81},
        {'name': 'Departments', 'key': 'departments', 'icon': 'bi bi-diagram-3', 'path': '/departments/', 'parent': 'group_admin', 'sequence': 82},
        {'name': 'Designations', 'key': 'designations', 'icon': 'bi bi-person-badge', 'path': '/designations/', 'parent': 'group_admin', 'sequence': 83},
        {'name': 'User Management', 'key': 'user_management', 'icon': 'bi bi-person-gear', 'path': '/users/', 'parent': 'group_admin', 'sequence': 84},
        {'name': 'Roles & Permissions', 'key': 'roles_permissions', 'icon': 'bi bi-shield-check', 'path': '/roles/', 'parent': 'group_admin', 'sequence': 85},
        # CLIENT PORTAL
        {'name': 'Portal Dashboard', 'key': 'portal_dashboard', 'icon': 'bi bi-speedometer2', 'path': '/portal/', 'parent': 'group_portal', 'sequence': 91},
        {'name': 'Portal Projects', 'key': 'portal_projects', 'icon': 'bi bi-kanban', 'path': '/portal/projects/', 'parent': 'group_portal', 'sequence': 92},
        {'name': 'Portal Invoices', 'key': 'portal_invoices', 'icon': 'bi bi-receipt', 'path': '/portal/invoices/', 'parent': 'group_portal', 'sequence': 93},
        {'name': 'Portal Documents', 'key': 'portal_documents', 'icon': 'bi bi-folder', 'path': '/portal/documents/', 'parent': 'group_portal', 'sequence': 94},
        {'name': 'Portal Tickets', 'key': 'portal_tickets', 'icon': 'bi bi-ticket', 'path': '/portal/tickets/', 'parent': 'group_portal', 'sequence': 95},
        # PLATFORM (Super Admin only)
        {'name': 'Companies', 'key': 'companies', 'icon': 'bi bi-building', 'path': '/companies/', 'parent': 'group_platform', 'sequence': 6},
        {'name': 'Packages', 'key': 'packages', 'icon': 'bi bi-box', 'path': '/packages/', 'parent': 'group_platform', 'sequence': 7},
        {'name': 'Subscriptions', 'key': 'subscriptions', 'icon': 'bi bi-credit-card-2-front', 'path': '/subscriptions/', 'parent': 'group_platform', 'sequence': 8},
    ]

    for m in modules_data:
        parent_obj = None
        if m['parent']:
            parent_obj = Module.objects.filter(key=m['parent']).first()
        mod, is_new = Module.objects.get_or_create(
            key=m['key'],
            defaults={
                'name': m['name'],
                'icon': m['icon'],
                'path': m['path'],
                'parent': parent_obj,
                'sequence': m['sequence'],
            }
        )
        if is_new:
            created.append(mod.name)
        else:
            # Update existing modules with new parent/sequence/icon
            mod.name = m['name']
            mod.icon = m['icon']
            mod.path = m['path']
            mod.parent = parent_obj
            mod.sequence = m['sequence']
            mod.save()

    all_modules = Module.objects.all()
    total_no_groups = all_modules.exclude(key__startswith='group_').count()
    print(f'Menu items: {total_no_groups} total, {len(created)} new created in this run')
    return all_modules


PERMISSION_TYPES = ['view', 'create', 'edit', 'delete', 'approve', 'export']


def seed_permissions(modules):
    created = 0
    for module in modules:
        for perm_type in PERMISSION_TYPES:
            codename = f'{perm_type}_{module.key}'
            name = f'{perm_type.title()} {module.name}'
            perm, is_new = Permission.objects.get_or_create(
                module=module,
                codename=codename,
                defaults={
                    'name': name,
                    'permission_type': perm_type,
                }
            )
            if is_new:
                created += 1
    print(f'Permissions: created {created} new')


SYSTEM_ROLES = {
    'super_admin': {
        'name': 'Super Administrator',
        'description': 'Unrestricted access to the entire system',
        'permissions': '__all__',
        'modules': '__all__',
    },
    'company_admin': {
        'name': 'Company Administrator',
        'description': 'Full access to all data within their company',
        'permissions': '__all__',
        'modules': '__all__',
    },
    'management': {
        'name': 'Management / Director',
        'description': 'Can view all projects, reports, revenue, and risks within their company',
        'permissions': ['view', 'export'],
        'modules': ['dashboard', 'clients', 'projects', 'tasks',
                     'meetings', 'documents',
                     'issues', 'risks', 'change_requests', 'support_tickets',
                     'invoices', 'payments', 'expenses',
                     'employees', 'timesheets', 'leave', 'attendance',
                     'reports'],
    },
    'delivery_manager': {
        'name': 'Delivery Manager',
        'description': 'Manages multiple projects, resources, delivery timelines',
        'permissions': ['view', 'export'],
        'modules': ['dashboard', 'clients', 'projects', 'tasks', 'milestones',
                     'deliverables', 'meetings', 'documents', 'team',
                     'issues', 'risks', 'change_requests', 'support_tickets',
                     'employees', 'timesheets', 'leave', 'attendance',
                     'reports'],
    },
    'project_manager': {
        'name': 'Project Manager',
        'description': 'Manages assigned projects, tasks, milestones, and team',
        'permissions': ['view', 'create', 'edit', 'export'],
        'modules': ['dashboard', 'clients', 'contacts', 'projects', 'tasks', 'milestones',
                     'deliverables', 'meetings', 'documents', 'team',
                     'issues', 'risks', 'change_requests', 'support_tickets',
                     'timesheets', 'leave', 'attendance',
                     'reports'],
    },
    'account_manager': {
        'name': 'Account Manager',
        'description': 'Client relationship, contracts, invoices, communication',
        'permissions': ['view', 'create', 'edit'],
        'modules': ['dashboard', 'clients', 'contacts', 'projects',
                     'meetings', 'documents',
                     'issues', 'support_tickets', 'change_requests',
                     'invoices', 'payments',
                     'reports'],
    },
    'employee': {
        'name': 'Employee / Staff',
        'description': 'Works on assigned tasks, logs timesheets, updates work',
        'permissions': ['view', 'create', 'edit'],
        'modules': ['dashboard', 'projects', 'tasks',
                     'timesheets', 'leave', 'attendance', 'expenses',
                     'meetings', 'documents'],
    },
    'hr_manager': {
        'name': 'HR / Resource Manager',
        'description': 'Manages employee profiles, leaves, attendance, allocations',
        'permissions': ['view', 'create', 'edit'],
        'modules': ['dashboard', 'employees', 'timesheets', 'leave', 'attendance',
                     'expenses', 'reports',
                     'departments', 'designations'],
    },
    'finance_user': {
        'name': 'Finance User',
        'description': 'Manages invoices, payments, billing, financial reports',
        'permissions': ['view', 'create', 'edit', 'export'],
        'modules': ['dashboard', 'clients', 'projects',
                     'invoices', 'payments', 'expenses', 'reports'],
    },
    'client_admin': {
        'name': 'Client Administrator',
        'description': 'Client-side admin - sees all their projects, approves deliverables',
        'permissions': ['view'],
        'modules': ['portal_dashboard', 'portal_projects', 'portal_invoices', 'portal_documents', 'portal_tickets'],
    },
    'client_user': {
        'name': 'Client User',
        'description': 'Limited client-side user - views assigned project details',
        'permissions': ['view'],
        'modules': ['portal_dashboard', 'portal_projects', 'portal_invoices', 'portal_documents', 'portal_tickets'],
    },
}


def seed_system_roles(modules):
    for category, role_data in SYSTEM_ROLES.items():
        role, created = Role.objects.get_or_create(
            category=category,
            is_system_role=True,
            company=None,
            defaults={
                'name': role_data['name'],
                'description': role_data['description'],
            }
        )
        # Determine which modules this role can access
        if role_data['modules'] == '__all__':
            allowed_modules = Module.objects.filter(is_active=True)
        else:
            allowed_modules = Module.objects.filter(key__in=role_data['modules'], is_active=True)

        # Determine which permission types
        if role_data['permissions'] == '__all__':
            perms = Permission.objects.filter(module__in=allowed_modules)
        else:
            perms = Permission.objects.filter(
                module__in=allowed_modules,
                permission_type__in=role_data['permissions']
            )
        role.permissions.set(perms)
        
        if created:
            print(f'Role created: {role.name}')
    print('System roles seeded')


def assign_superadmin_role():
    """Assign super_admin role to all superusers."""
    super_admin_role = Role.objects.filter(category='super_admin', is_system_role=True).first()
    if super_admin_role:
        superusers = User.objects.filter(is_superuser=True)
        for user in superusers:
            user.roles.add(super_admin_role)
        print(f'Superadmin role assigned to {superusers.count()} users')


def seed_operational_prerequisites():
    """Seed minimum records required for core operational workflows."""
    leave_created = 0
    expense_created = 0
    for company in Company.objects.all():
        _, new_leave = LeavePolicy.objects.get_or_create(
            company=company,
            name='Annual Leave',
            leave_type='annual',
            defaults={
                'frequency': 'yearly',
                'max_days': 21,
                'is_paid': True,
                'is_carry_forward': False,
                'requires_approval': True,
                'min_notice_days': 1,
                'is_active': True,
                'description': 'Default annual leave policy seeded for operational testing.',
            },
        )
        if new_leave:
            leave_created += 1

        _, new_expense = ExpenseCategory.objects.get_or_create(
            company=company,
            name='General',
            defaults={
                'description': 'Default expense category seeded for operational testing.',
                'is_active': True,
            },
        )
        if new_expense:
            expense_created += 1
    print(f'Operational prerequisites: LeavePolicy +{leave_created}, ExpenseCategory +{expense_created}')


if __name__ == '__main__':
    print('=== Seeding RBAC System ===')
    modules = seed_modules()
    seed_permissions(modules)
    seed_system_roles(modules)
    assign_superadmin_role()
    seed_operational_prerequisites()
    print('=== Seeding Complete ===')
