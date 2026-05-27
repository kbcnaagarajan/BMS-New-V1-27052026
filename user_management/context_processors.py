"""
Context processors for injecting RBAC data into Django templates.
"""
from .rbac import build_user_menu


def rbac_context(request):
    """Expose RBAC data to all templates."""
    context = {
        'rbac_menu': [],
        'rbac_permissions': {},
        'is_super_admin': False,
        'is_company_admin': False,
        'user_type': '',
        'company_name': '',
    }

    if hasattr(request, 'rbac') and request.rbac:
        context['rbac_menu'] = request.rbac.get('menu', [])
        context['rbac_permissions'] = request.rbac.get('permissions', {})
        context['is_super_admin'] = request.rbac.get('is_super_admin', False)
        context['is_company_admin'] = request.rbac.get('is_company_admin', False)
        context['user_type'] = request.rbac.get('user_type', '')
        context['company_id'] = request.rbac.get('company_id', None)
        context['company_name'] = request.rbac.get('company_name', '')

    return context
