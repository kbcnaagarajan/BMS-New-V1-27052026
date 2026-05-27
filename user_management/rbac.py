"""
RBAC Utilities - Permission checking, menu building, and scope enforcement.
"""
from django.db.models import Q

from user_management.models import Module


def build_user_menu(user):
    """Build the navigation menu for a user based on their module permissions."""
    accessible = user.get_accessible_modules()
    all_modules = Module.objects.filter(is_active=True, is_menu_item=True)
    menu = []

    # Standalone items (Dashboard)
    for module in all_modules.filter(parent__isnull=True, is_menu_item=True).exclude(key__startswith='group_').order_by('sequence'):
        if module in accessible:
            menu.append({
                'key': module.key,
                'name': module.name,
                'icon': module.icon,
                'path': module.path,
                'permissions': user.get_module_permissions(module.key),
                'children': [],
            })

    # Grouped items
    for group in all_modules.filter(parent__isnull=True, key__startswith='group_').order_by('sequence'):
        children = all_modules.filter(parent=group, is_menu_item=True).order_by('sequence')
        visible_children = []
        for child in children:
            if child in accessible:
                visible_children.append({
                    'key': child.key,
                    'name': child.name,
                    'icon': child.icon,
                    'path': child.path,
                    'permissions': user.get_module_permissions(child.key),
                })
        if visible_children:
            menu.append({
                'key': group.key,
                'name': group.name,
                'icon': group.icon,
                'path': group.path,
                'permissions': [],
                'children': visible_children,
            })
    return menu


def get_user_scope_filter(user, model_class):
    """
    Get the appropriate filter kwargs for company-scoped queries.
    Returns a dict that can be used as: Model.objects.filter(**scope_filter)

    Rules:
    - Superadmin: no filter (sees all)
    - Company admin: filter by own company
    - Regular user: filter by own company (narrowed further in view logic)
    """
    if user.is_superuser:
        return {}
    if user.company:
        # Check if model has a 'company' field
        if hasattr(model_class, 'company'):
            return {'company': user.company}
        # Check if model has a 'client' field with client->company chain
        if hasattr(model_class, 'client') and hasattr(model_class.client.field.related_model, 'company'):
            return {'client__company': user.company}
        # Check if model has 'project' field with project->client->company chain
        if hasattr(model_class, 'project'):
            project_model = model_class.project.field.related_model
            if hasattr(project_model, 'client'):
                client_model = project_model.client.field.related_model
                if hasattr(client_model, 'company'):
                    return {'project__client__company': user.company}
        # Fallback: filter by user's company-related users
        if hasattr(model_class, 'employee'):
            return {'employee__company': user.company}
        if hasattr(model_class, 'user'):
            return {'user__company': user.company}
    return {}


SCOPE_CONFIG = {
    'client_crm.Client': 'company',
    'client_crm.ClientContact': 'client__company',
    'client_crm.ClientLocation': 'client__company',
    'client_crm.ClientContract': 'client__company',
    'client_crm.ClientNote': 'client__company',
    'client_crm.ClientCommunicationLog': 'client__company',

    'project_360.Project': 'client__company',
    'project_360.ProjectTeamMember': 'project__client__company',
    'project_360.ProjectMilestone': 'project__client__company',
    'project_360.ProjectTask': 'project__client__company',
    'project_360.TaskComment': 'task__project__client__company',
    'project_360.TaskAttachment': 'task__project__client__company',
    'project_360.ProjectDeliverable': 'project__client__company',
    'project_360.ProjectStatusUpdate': 'project__client__company',
    'project_360.ProjectDocument': 'project__client__company',
    'project_360.ProjectActivityLog': 'project__client__company',
    'project_360.ProjectClosureChecklist': 'project__client__company',

    'employee_operations.Attendance': 'employee__company',
    'employee_operations.LeavePolicy': 'company',
    'employee_operations.LeaveBalance': 'employee__company',
    'employee_operations.LeaveRequest': 'employee__company',
    'employee_operations.WFHRequest': 'employee__company',
    'employee_operations.Timesheet': 'employee__company',
    'employee_operations.TimesheetEntry': 'project__client__company',
    'employee_operations.ExpenseCategory': 'company',
    'employee_operations.Expense': 'employee__company',

    'issues_risks.ProjectIssue': 'project__client__company',
    'issues_risks.ProjectRisk': 'project__client__company',
    'issues_risks.ChangeRequest': 'project__client__company',
    'issues_risks.SupportTicket': 'project__client__company',

    'billing.BillingMilestone': 'project__client__company',
    'billing.Invoice': 'project__client__company',
    'billing.Payment': 'project__client__company',

    'meetings_documents.Meeting': 'project__client__company',
    'meetings_documents.MeetingActionItem': 'meeting__project__client__company',
    'meetings_documents.Document': 'project__client__company',
    'meetings_documents.Notification': 'user__company',

    'user_management.User': 'company',
    'user_management.Company': 'id',
    'user_management.Department': 'company',
    'user_management.Designation': 'company',
    'user_management.Role': 'company',
    'user_management.Module': '',
    'user_management.Permission': '',
}


def get_company_scope_filter(user, model):
    """
    Return a Q filter object for company-scoped queries.
    Uses the SCOPE_CONFIG to determine the filter path.
    """
    if user.is_superuser:
        return Q()

    if not user.company:
        return Q(pk=None)  # Return nothing if user has no company

    model_label = f'{model._meta.app_label}.{model.__name__}'
    scope_path = SCOPE_CONFIG.get(model_label)

    if not scope_path:
        return Q()

    # Build Q filter from path like 'project__client__company'
    return Q(**{scope_path: user.company})


def get_company_filter_kwargs(user, model):
    """Simple version - returns filter kwargs or empty dict."""
    if user.is_superuser:
        return {}

    if not user.company:
        return {'pk': None}

    model_label = f'{model._meta.app_label}.{model.__name__}'
    scope_path = SCOPE_CONFIG.get(model_label)

    if not scope_path:
        return {}

    return {scope_path: user.company}
