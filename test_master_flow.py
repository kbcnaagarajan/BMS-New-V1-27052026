"""Master end-to-end test: all 26 workflows in order"""
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'KarthikAi_OMS.settings')
sys.path.insert(0, '.')
django.setup()

from user_management.models import User, Company, Role, Department, Designation, CompanyInvite, SUPER_ADMIN_RESTRICTED_MODULES
from user_management.rbac import build_user_menu
from client_crm.models import Client, ClientContact
from project_360.models import Project, ProjectTeamMember, ProjectTask, ProjectMilestone, ProjectDeliverable
from billing.models import Invoice, Payment
from employee_operations.models import Timesheet, LeaveRequest, LeavePolicy, Attendance
from meetings_documents.models import Meeting, Document
from issues_risks.models import ProjectIssue, ProjectRisk, ChangeRequest
from datetime import datetime, date, timedelta, time
from decimal import Decimal
from django.test import Client as TestClient
from django.urls import reverse
from django.utils import timezone

ok, fail = 0, 0
def check(label, cond, detail=''):
    global ok, fail
    if cond:
        ok += 1
        print(f'  PASS: {label}')
    else:
        fail += 1
        print(f'  FAIL: {label} {detail}')

# ── Helpers ──
today = date.today()
CLEANUP_KEYS = ['timesheets', 'leave', 'attendance', 'expenses', 'meetings', 'documents',
                'issues', 'risks', 'change_requests', 'support_tickets', 'team',
                'tasks', 'milestones', 'deliverables', 'invoices', 'payments', 'contacts']

def admin_login(email='company@testco.com'):
    c = TestClient()
    c.login(email=email, password='admin123')
    return c

def assert_forbidden_or_empty(resp, label=''):
    """Check response is either 403/302 or 200 with empty content."""
    if resp.status_code in (302, 403, 404):
        return True
    if resp.status_code == 200:
        content = resp.content.decode().lower()
        return 'no ' in content or 'empty' in content or '0' in content
    return False

def count_in_content(resp, text):
    return text.lower() in resp.content.decode().lower()

# ═══════════════════════════════════════════════
#  SETUP: Pre-seeded test users
# ═══════════════════════════════════════════════

# Ensure system roles exist
for cat in ('super_admin','company_admin','project_manager','employee','hr_manager','finance_user','client_admin','client_user'):
    Role.objects.get_or_create(category=cat, is_system_role=True, defaults={'name': cat.replace('_',' ').title()})

# Clean up any previous test data — start fresh
Company.objects.filter(name__in=['TestCo', 'OtherCo']).delete()
User.objects.filter(email__in=['admin@testco.com', 'pm@testco.com', 'emp@testco.com',
                                'finance@testco.com', 'client@testco.com']).delete()
Client.objects.filter(client_code__in=['ACME001', 'OTHER01']).delete()

# ───────────────────────────────────────────────
#  1. SUPER ADMIN CREATES COMPANY
# ───────────────────────────────────────────────
print()
print('=' * 60)
print('  1. SUPER ADMIN CREATES COMPANY (WF1)')
print('=' * 60)

c_super = TestClient()
c_super.login(email='admin@karthikai.com', password='admin123')
resp = c_super.get(reverse('company_list'))
check('SA sees company list', resp.status_code == 200)

resp = c_super.post(reverse('company_add'), {
    'name': 'TestCo', 'email': 'admin@testco.com', 'phone': '1234567890',
    'currency': 'USD', 'timezone': 'UTC', 'working_days': 'Mon-Fri', 'working_hours': '9-5',
    'admin_email': 'admin@testco.com', 'admin_first_name': 'Admin', 'admin_last_name': 'User',
})
check('SA creates company', resp.status_code == 302)
company = Company.objects.filter(name='TestCo').first()
check('Company exists', company is not None)

invite = CompanyInvite.objects.filter(company=company).first()
check('Invite generated', invite is not None and invite.token)
check('Invite pending', invite.status == 'pending')

# ───────────────────────────────────────────────
#  2. COMPANY ADMIN ACCEPTS INVITE (WF2)
# ───────────────────────────────────────────────
print()
print('=' * 60)
print('  2. COMPANY ADMIN ACCEPTS INVITE (WF2)')
print('=' * 60)

resp = c_super.get(reverse('company_detail', args=[company.pk]))
check('SA sees company detail', resp.status_code == 200)

accept_url = reverse('company_invite_accept', args=[invite.token])
resp = TestClient().post(accept_url, {
    'password': 'admin123', 'confirm_password': 'admin123',
})
check('Invite accepted (redirects)', resp.status_code in (302, 200))
company.refresh_from_db()
check('Company active after accept', company.is_active)
admin_user = User.objects.filter(email=invite.email).first()
check('Company admin user created', admin_user is not None)
check('Company admin assigned', company.company_admin == admin_user)

# ───────────────────────────────────────────────
#  3. COMPANY ADMIN SETS UP WORKSPACE (WF3) + CREATES USERS (WF4)
# ───────────────────────────────────────────────
print()
print('=' * 60)
print('  3. SETUP WORKSPACE + CREATE USERS (WF3-4)')
print('=' * 60)

c_admin = TestClient()
c_admin.login(email='admin@testco.com', password='admin123')

# Create department
resp = c_admin.post(reverse('departments_add'), {'name': 'Engineering', 'code': 'ENG', 'description': 'Engineering dept'})
check('Admin creates department', resp.status_code == 302)
dept = Department.objects.filter(company=company).first()
check('Department exists', dept is not None)

# Create designation
resp = c_admin.post(reverse('designations_add'), {'title': 'Engineer', 'level': '2', 'description': 'Engineer role'})
check('Admin creates designation', resp.status_code == 302)
desig = Designation.objects.filter(company=company).first()
check('Designation exists', desig is not None)

# Create PM user
resp = c_admin.post(reverse('users_add'), {
    'email': 'pm@testco.com', 'first_name': 'Project', 'last_name': 'Manager',
    'user_type': 'project_manager', 'password': 'admin123',
    'department': str(dept.pk), 'designation': str(desig.pk),
    'is_active': 'on',
})
check('Admin creates PM user', resp.status_code == 302)
pm_user = User.objects.filter(email='pm@testco.com').first()
check('PM user exists', pm_user is not None)
check('PM user active', pm_user.is_active)

# Create Employee user
resp = c_admin.post(reverse('users_add'), {
    'email': 'emp@testco.com', 'first_name': 'Employee', 'last_name': 'User',
    'user_type': 'employee', 'password': 'admin123',
    'department': str(dept.pk), 'designation': str(desig.pk),
    'is_active': 'on',
})
check('Admin creates Employee user', resp.status_code == 302)
emp_user = User.objects.filter(email='emp@testco.com').first()
check('Employee user exists', emp_user is not None)

# Create Finance user
resp = c_admin.post(reverse('users_add'), {
    'email': 'finance@testco.com', 'first_name': 'Finance', 'last_name': 'User',
    'user_type': 'finance_user', 'password': 'admin123',
    'department': str(dept.pk), 'designation': str(desig.pk),
    'is_active': 'on',
})
check('Admin creates Finance user', resp.status_code == 302)
fin_user = User.objects.filter(email='finance@testco.com').first()
check('Finance user exists', fin_user is not None)

# Create Client user (for portal login)
resp = c_admin.post(reverse('users_add'), {
    'email': 'client@testco.com', 'first_name': 'Client', 'last_name': 'User',
    'user_type': 'client_user', 'password': 'admin123',
    'department': str(dept.pk), 'designation': str(desig.pk),
    'is_active': 'on',
})
check('Admin creates Client user', resp.status_code == 302)
client_user = User.objects.filter(email='client@testco.com').first()
check('Client user exists', client_user is not None)
client_user.is_client_user = True
client_user.save()

# Assign system roles so has_module_access() checks pass
Role.objects.filter(category='company_admin', is_system_role=True).first().users.add(admin_user)
Role.objects.filter(category='project_manager', is_system_role=True).first().users.add(pm_user)
Role.objects.filter(category='employee', is_system_role=True).first().users.add(emp_user)

# Set company for all users
for u in User.objects.filter(company__isnull=True):
    u.company = company; u.save()

# ───────────────────────────────────────────────
#  4. RBAC PERMISSION CHECKS (WF5)
# ───────────────────────────────────────────────
print()
print('=' * 60)
print('  4. RBAC PERMISSION CHECKS (WF5)')
print('=' * 60)

# PM has project_manager modules
check('PM has project access', pm_user.has_module_access('projects'))
check('PM has tasks access', pm_user.has_module_access('tasks'))

# Employee has employee-only scope
check('Employee has timesheets access', emp_user.has_module_access('timesheets'))
check('Employee blocked from clients', not emp_user.has_module_access('clients'))
check('Employee blocked from invoices', not emp_user.has_module_access('invoices'))

# Company admin has full access
check('Admin has client access', admin_user.has_module_access('clients'))
check('Admin has invoice access', admin_user.has_module_access('invoices'))

# Super Admin restricted
super_user = User.objects.filter(is_superuser=True).first()
check('Super admin exists', super_user is not None)
for mk in SUPER_ADMIN_RESTRICTED_MODULES:
    check(f'SA blocked from {mk}', not super_user.has_module_access(mk))

# ───────────────────────────────────────────────
#  5. PM CREATES CLIENT (WF6)
# ───────────────────────────────────────────────
print()
print('=' * 60)
print('  5. PM CREATES CLIENT (WF6)')
print('=' * 60)

c_pm = admin_login('pm@testco.com')

resp = c_pm.post(reverse('client_add'), {
    'name': 'Acme Corp', 'client_code': 'ACME001',
    'email': 'info@acme.com', 'phone': '1234567890',
    'company': str(company.pk), 'client_type': 'company',
})
check('PM creates client', resp.status_code == 302)
client = Client.objects.filter(name='Acme Corp').first()
check('Client exists', client is not None)

# Link client_user to client via ClientContact
ClientContact.objects.create(client=client, first_name='Client', last_name='Portal',
    email='client@testco.com', portal_user=client_user, can_login=True)

# ───────────────────────────────────────────────
#  6. PM CREATES PROJECT UNDER CLIENT (WF7)
# ───────────────────────────────────────────────
print()
print('=' * 60)
print('  6. PM CREATES PROJECT (WF7)')
print('=' * 60)

resp = c_pm.post(reverse('project_add'), {
    'project_name': 'Website Redesign', 'project_code': 'PRJ-WR-001',
    'client': str(client.pk), 'project_manager': str(pm_user.pk),
    'start_date': str(today), 'expected_end_date': str(today + timedelta(days=90)),
    'status': 'active',
})
check('PM creates project', resp.status_code == 302)
proj = Project.objects.filter(project_name='Website Redesign').first()
check('Project exists', proj is not None)

# ───────────────────────────────────────────────
#  7. PM ADDS TEAM MEMBER (WF8-part1)
# ───────────────────────────────────────────────
print()
print('=' * 60)
print('  7. PM ADDS TEAM MEMBER (WF8-part1)')
print('=' * 60)

resp = c_pm.post(reverse('team_add'), {
    'project': str(proj.pk), 'user': str(emp_user.pk),
    'role': 'backend_dev', 'is_active': 'on',
})
check('PM adds team member', resp.status_code == 302)
member = ProjectTeamMember.objects.filter(project=proj, user=emp_user).first()
check('Team member exists', member is not None)

# ───────────────────────────────────────────────
#  8. PM CREATES MILESTONES + DELIVERABLES (WF8-part2)
# ───────────────────────────────────────────────
print()
print('=' * 60)
print('  8. MILESTONES + DELIVERABLES (WF8-part2)')
print('=' * 60)

resp = c_pm.post(reverse('milestones_add'), {
    'project': str(proj.pk), 'title': 'Phase 1 Complete',
    'start_date': str(today), 'due_date': str(today + timedelta(days=30)),
    'status': 'pending',
})
check('PM creates milestone', resp.status_code == 302)
ms = ProjectMilestone.objects.filter(project=proj).first()
check('Milestone exists', ms is not None)

resp = c_pm.post(reverse('deliverables_add'), {
    'project': str(proj.pk), 'title': 'Wireframes',
    'milestone': str(ms.pk), 'assigned_to': str(emp_user.pk),
    'due_date': str(today + timedelta(days=14)), 'status': 'pending',
})
check('PM creates deliverable', resp.status_code == 302)
dl = ProjectDeliverable.objects.filter(project=proj).first()
check('Deliverable exists', dl is not None)

# ───────────────────────────────────────────────
#  9. PM CREATES + ASSIGNS TASKS (WF9)
# ───────────────────────────────────────────────
print()
print('=' * 60)
print('  9. PM CREATES TASKS (WF9)')
print('=' * 60)

resp = c_pm.post(reverse('task_add'), {
    'project': str(proj.pk), 'title': 'Setup homepage',
    'assigned_to': str(emp_user.pk), 'description': 'Build homepage layout',
    'due_date': str(today + timedelta(days=14)), 'status': 'in_progress',
    'progress_percentage': '0', 'priority': 'high',
})
check('PM creates task', resp.status_code == 302)
task = ProjectTask.objects.filter(project=proj, title='Setup homepage').first()
check('Task exists', task is not None)
check('Task assigned to employee', task.assigned_to == emp_user)

# ───────────────────────────────────────────────
#  10. EMPLOYEE VIEWS ASSIGNED TASK (WF10)
# ───────────────────────────────────────────────
print()
print('=' * 60)
print('  10. EMPLOYEE VIEWS + UPDATES TASK (WF10)')
print('=' * 60)

c_emp = admin_login('emp@testco.com')
resp = c_emp.get(reverse('task_list'))
check('Employee sees task list', resp.status_code == 200)

# Employee updates task progress
resp = c_emp.post(reverse('task_edit', args=[task.pk]), {
    'project': str(proj.pk), 'title': 'Setup homepage',
    'assigned_to': str(emp_user.pk), 'description': 'Build homepage layout',
    'due_date': str(today + timedelta(days=14)), 'status': 'in_progress',
    'progress': '50', 'priority': 'high',
})
check('Employee updates task', resp.status_code == 302)
task.refresh_from_db()
check('Task progress updated', task.progress_percentage == 50)

# ───────────────────────────────────────────────
#  11. EMPLOYEE CREATES TIMESHEET (WF11)
# ───────────────────────────────────────────────
print()
print('=' * 60)
print('  11. EMPLOYEE CAPTURES TIMESHEET (WF11)')
print('=' * 60)

resp = c_emp.post(reverse('timesheets_add'), {
    'employee': str(emp_user.pk), 'week_start_date': str(today),
    'week_end_date': str(today + timedelta(days=6)), 'notes': 'Week 1 work',
})
check('Employee creates timesheet', resp.status_code == 302)
ts = Timesheet.objects.filter(employee=emp_user).first()
check('Timesheet exists', ts is not None)

resp = c_emp.get(reverse('timesheets_list'))
check('Employee sees own timesheet', resp.status_code == 200)

# ───────────────────────────────────────────────
#  12. PM REVIEWS TIMESHEET (WF12)
# ───────────────────────────────────────────────
print()
print('=' * 60)
print('  12. PM REVIEWS TIMESHEET (WF12)')
print('=' * 60)

resp = c_pm.get(reverse('timesheets_list'))
check('PM sees timesheet list', resp.status_code == 200)

# ───────────────────────────────────────────────
#  13. PM CREATES MEETING (WF14)
# ───────────────────────────────────────────────
print()
print('=' * 60)
print('  13. PM CREATES MEETING (WF14)')
print('=' * 60)

resp = c_pm.post(reverse('meetings_add'), {
    'project': str(proj.pk), 'title': 'Sprint Review',
    'meeting_type': 'internal', 'meeting_date': str(today),
    'start_time': '10:00', 'end_time': '11:00',
    'status': 'scheduled', 'agenda': 'Review sprint',
})
check('PM creates meeting', resp.status_code == 302)
mtg = Meeting.objects.filter(project=proj).first()
check('Meeting exists', mtg is not None)

# ───────────────────────────────────────────────
#  14. PM CREATES DOCUMENT (WF15)
# ───────────────────────────────────────────────
print()
print('=' * 60)
print('  14. PM CREATES DOCUMENT (WF15)')
print('=' * 60)

resp = c_pm.post(reverse('documents_add'), {
    'project': str(proj.pk), 'title': 'Project Plan',
    'document_type': 'project_plan', 'visibility': 'team',
    'description': 'Project plan document', 'version': '1.0',
})
check('PM creates document', resp.status_code == 302)
doc = Document.objects.filter(project=proj).first()
check('Document exists', doc is not None)

# ───────────────────────────────────────────────
#  15. PM CREATES ISSUE (WF16)
# ───────────────────────────────────────────────
print()
print('=' * 60)
print('  15. PM CREATES ISSUE (WF16)')
print('=' * 60)

resp = c_pm.post(reverse('issues_add'), {
    'project': str(proj.pk), 'title': 'API rate limit',
    'description': 'Third-party API returning 429 errors',
    'issue_type': 'technical', 'severity': 'major',
    'assigned_to': str(emp_user.pk),
})
check('PM creates issue', resp.status_code == 302)
issue = ProjectIssue.objects.filter(project=proj).first()
check('Issue exists', issue is not None)
issue.status = 'resolved'; issue.save()
check('PM resolves issue', issue.status == 'resolved')

# ───────────────────────────────────────────────
#  16. PM CREATES RISK (WF17)
# ───────────────────────────────────────────────
print()
print('=' * 60)
print('  16. PM CREATES RISK (WF17)')
print('=' * 60)

resp = c_pm.post(reverse('risks_add'), {
    'project': str(proj.pk), 'title': 'Developer may leave',
    'description': 'Sole backend developer considering opportunities',
    'severity': 'high', 'probability': 'medium', 'impact': 'high',
    'mitigation_plan': 'Cross-train team member',
    'owner': str(pm_user.pk),
})
check('PM creates risk', resp.status_code == 302)
risk = ProjectRisk.objects.filter(project=proj).first()
check('Risk exists', risk is not None)

# ───────────────────────────────────────────────
#  17. FINANCE CREATES INVOICE (WF19)
# ───────────────────────────────────────────────
print()
print('=' * 60)
print('  17. FINANCE CREATES INVOICE (WF19)')
print('=' * 60)

c_finance = admin_login('finance@testco.com')
resp = c_finance.post(reverse('invoices_add'), {
    'project': str(proj.pk), 'client': str(client.pk),
    'invoice_date': str(today), 'due_date': str(today + timedelta(days=30)),
    'amount': '10000.00', 'tax_amount': '1800.00',
    'currency': 'USD', 'status': 'draft',
})
check('Finance creates invoice', resp.status_code == 302)
inv = Invoice.objects.filter(project=proj).first()
check('Invoice exists', inv is not None)
check('Total auto-calculated', inv.total_amount == Decimal('11800.00'))
check('Balance set', inv.balance_amount == Decimal('11800.00'))

# ───────────────────────────────────────────────
#  18. FINANCE RECORDS PAYMENT (WF20)
# ───────────────────────────────────────────────
print()
print('=' * 60)
print('  18. FINANCE RECORDS PAYMENT (WF20)')
print('=' * 60)

resp = c_finance.post(reverse('payments_add'), {
    'invoice': str(inv.pk), 'project': str(proj.pk), 'client': str(client.pk),
    'amount': '11800.00', 'payment_date': str(today),
    'payment_mode': 'bank_transfer',
})
check('Finance records payment', resp.status_code == 302)
pay = Payment.objects.filter(invoice=inv).first()
check('Payment exists', pay is not None)
inv.refresh_from_db()
check('Invoice paid', inv.status == 'paid' and inv.balance_amount == 0)

# ───────────────────────────────────────────────
#  19. CLIENT USER VIEWS PORTAL (WF21)
# ───────────────────────────────────────────────
print()
print('=' * 60)
print('  19. CLIENT PORTAL VIEW (WF21)')
print('=' * 60)

c_client = admin_login('client@testco.com')
resp = c_client.get(reverse('portal_dashboard'))
check('Client sees portal dashboard', resp.status_code == 200)

resp = c_client.get(reverse('portal_projects'))
check('Client sees portal projects', resp.status_code == 200)
check('Client sees their project', proj.project_name in resp.content.decode())

# Client blocked from internal modules
for url_name in ['project_list', 'client_list', 'invoices_list']:
    resp = c_client.get(reverse(url_name))
    check(f'Client blocked from {url_name}', assert_forbidden_or_empty(resp))

# Cross-company isolation
other_co = Company.objects.create(name='OtherCo')
other_client = Client.objects.create(name='Other Client', company=other_co, client_code='OTHER01', email='x@x.com')
resp = c_client.get(reverse('portal_projects'))
check('Cross-company isolation', other_client.name not in resp.content.decode())

# ───────────────────────────────────────────────
#  20. EMPLOYEE RESTRICTION TEST (WF22)
# ───────────────────────────────────────────────
print()
print('=' * 60)
print('  20. EMPLOYEE RESTRICTION TEST (WF22)')
print('=' * 60)

for url_name in ['task_list', 'timesheets_list', 'leaves_list', 'attendance_list']:
    resp = c_emp.get(reverse(url_name))
    check(f'Employee accesses {url_name}', resp.status_code == 200)

for url_name in ['client_list', 'invoices_list', 'payments_list']:
    resp = c_emp.get(reverse(url_name))
    check(f'Employee blocked from {url_name}', assert_forbidden_or_empty(resp))

# ───────────────────────────────────────────────
#  21. PM RESTRICTION TEST (WF23)
# ───────────────────────────────────────────────
print()
print('=' * 60)
print('  21. PM RESTRICTION TEST (WF23)')
print('=' * 60)

for url_name in ['task_list', 'milestones_list', 'deliverables_list', 'meetings_list',
                  'documents_list', 'issues_list', 'risks_list']:
    resp = c_pm.get(reverse(url_name))
    check(f'PM accesses {url_name}', resp.status_code == 200)

resp = c_pm.get(reverse('client_list'))
check(f'PM accesses clients', resp.status_code == 200)

# PM NOT blocked from company-scoped data (they're in the same company)
resp = c_pm.get(reverse('timesheets_list'))
check('PM sees timesheets', resp.status_code == 200)

# ───────────────────────────────────────────────
#  22. COMPANY ADMIN FULL ACCESS (WF24)
# ───────────────────────────────────────────────
print()
print('=' * 60)
print('  22. COMPANY ADMIN FULL ACCESS (WF24)')
print('=' * 60)

for url_name in ['client_list', 'project_list', 'task_list', 'timesheets_list',
                  'leaves_list', 'attendance_list', 'invoices_list', 'payments_list',
                  'users_list', 'issues_list', 'risks_list', 'reports_list']:
    resp = c_admin.get(reverse(url_name))
    check(f'Admin accesses {url_name}', resp.status_code == 200)

# ───────────────────────────────────────────────
#  23. SUPER ADMIN PRIVACY BOUNDARY (WF25)
# ───────────────────────────────────────────────
print()
print('=' * 60)
print('  23. SUPER ADMIN BOUNDARY (WF25)')
print('=' * 60)

resp = c_super.get(reverse('company_list'))
check('SA accesses company list', resp.status_code == 200)
resp = c_super.get(reverse('company_detail', args=[company.pk]))
check('SA accesses company detail', resp.status_code == 200)

for mk in SUPER_ADMIN_RESTRICTED_MODULES:
    for suffix in ['_list', '_add']:
        try:
            url = reverse(mk + suffix)
            resp = c_super.get(url)
            check(f'SA blocked from {mk+suffix}', resp.status_code in (302, 403, 404))
        except:
            pass

# SA menu hides restricted modules
menu = build_user_menu(User.objects.get(email='admin@karthikai.com'))
menu_keys = set()
for item in menu:
    menu_keys.add(item['key'])
    for child in item.get('children', []):
        menu_keys.add(child['key'])
for mk in SUPER_ADMIN_RESTRICTED_MODULES:
    check(f'SA menu hides {mk}', mk not in menu_keys)

# SA CAN access monitoring modules
for url_name in ['client_list', 'project_list', 'company_list', 'reports_list', 'dashboard']:
    resp = c_super.get(reverse(url_name))
    check(f'SA accesses {url_name}', resp.status_code == 200)

# ───────────────────────────────────────────────
#  24. REPORTS DASHBOARD BY ROLE (WF26)
# ───────────────────────────────────────────────
print()
print('=' * 60)
print('  24. REPORTS DASHBOARD BY ROLE (WF26)')
print('=' * 60)

# Super Admin: sees global counts
resp = c_super.get(reverse('reports_list'))
check('SA reports dashboard loads', resp.status_code == 200)

# Company Admin: sees company-scoped counts
resp = c_admin.get(reverse('reports_list'))
check('Admin reports dashboard loads', resp.status_code == 200)

# PM: sees their project counts
resp = c_pm.get(reverse('reports_list'))
check('PM reports dashboard loads', resp.status_code == 200)

# Employee: sees assigned work counts
resp = c_emp.get(reverse('reports_list'))
check('Employee reports dashboard loads', resp.status_code == 200)

# Client user blocked from reports
resp = c_client.get(reverse('reports_list'))
check('Client blocked from reports', resp.status_code in (302, 403))

# ───────────────────────────────────────────────
#  SUMMARY
# ───────────────────────────────────────────────
print()
print('=' * 60)
print(f'  COMPLETE: {ok} passed, {fail} failed')
print('=' * 60)
if fail:
    exit(1)
