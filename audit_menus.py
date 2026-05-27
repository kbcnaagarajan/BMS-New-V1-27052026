"""Audit: verify each user profile sees the correct menu modules"""
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'KarthikAi_OMS.settings')
sys.path.insert(0, '.')
django.setup()

from user_management.models import User, Module, SA_ALLOWED_MODULES
from user_management.rbac import build_user_menu

EMAILS = {
    'super_admin': 'admin@karthikai.com',
    'company_admin': 'admin@testco.com',
    'project_manager': 'pm@testco.com',
    'employee': 'emp@testco.com',
    'finance_user': 'finance@testco.com',
    'client_user': 'client@testco.com',
}

EXPECTED = {
    'super_admin': set(SA_ALLOWED_MODULES),
    'company_admin': '__all__',
    'management': {'dashboard', 'clients', 'projects', 'tasks',
                    'meetings', 'documents',
                    'issues', 'risks', 'change_requests', 'support_tickets',
                    'invoices', 'payments', 'expenses',
                    'employees', 'timesheets', 'leave', 'attendance',
                    'reports'},
    'delivery_manager': {'dashboard', 'clients', 'projects', 'tasks', 'milestones',
                          'deliverables', 'meetings', 'documents', 'team',
                          'issues', 'risks', 'change_requests', 'support_tickets',
                          'employees', 'timesheets', 'leave', 'attendance',
                          'reports'},
    'project_manager': {'dashboard', 'clients', 'contacts', 'projects', 'tasks',
                         'milestones', 'deliverables', 'meetings', 'documents', 'team',
                         'issues', 'risks', 'change_requests', 'support_tickets',
                         'timesheets', 'leave', 'attendance',
                         'reports'},
    'account_manager': {'dashboard', 'clients', 'contacts', 'projects',
                         'meetings', 'documents',
                         'issues', 'support_tickets', 'change_requests',
                         'invoices', 'payments',
                         'reports'},
    'employee': {'dashboard', 'projects', 'tasks',
                  'timesheets', 'leave', 'attendance', 'expenses',
                  'meetings', 'documents'},
    'hr_manager': {'dashboard', 'employees', 'timesheets', 'leave', 'attendance',
                    'expenses', 'reports',
                    'departments', 'designations'},
    'finance_user': {'dashboard', 'clients', 'projects',
                      'invoices', 'payments', 'expenses',
                      'reports'},
    'client_admin': {'portal_dashboard', 'portal_projects'},
    'client_user': {'portal_dashboard', 'portal_projects'},
}

def get_menu_keys(user):
    menu = build_user_menu(user)
    keys = set()
    for item in menu:
        key = item['key']
        if not key.startswith('group_'):
            keys.add(key)
        for child in item.get('children', []):
            ck = child['key']
            if not ck.startswith('group_'):
                keys.add(ck)
    return keys

ok, fail = 0, 0
for label, email in EMAILS.items():
    user = User.objects.get(email=email)
    keys = get_menu_keys(user)
    expected = EXPECTED[label]

    if expected == '__all__':
        total = Module.objects.filter(is_active=True).exclude(key__startswith='group_').count()
        print(f'  [{label}] {email}: {len(keys)}/{total} modules (all)')
        ok += 1
        continue

    extra = keys - expected
    missing = expected - keys

    if extra or missing:
        fail += 1
        status = 'FAIL'
    else:
        ok += 1
        status = 'PASS'

    print(f'  [{status}] {label} ({email}):')
    if missing:
        print(f'         Missing: {sorted(missing)}')
    if extra:
        print(f'         Extra:   {sorted(extra)}')
    if not extra and not missing:
        print(f'         All {len(keys)} expected modules match ({len(keys)} total)')

print(f'\n{ok} passed, {fail} failed')
if fail:
    exit(1)
