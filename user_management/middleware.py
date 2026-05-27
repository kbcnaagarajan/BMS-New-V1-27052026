"""
Middleware for injecting RBAC context into requests.
Provides user permissions, accessible modules, and navigation menu.
"""
from django.utils.deprecation import MiddlewareMixin
from django.db import connection
from .rbac import build_user_menu


class RBACMiddleware(MiddlewareMixin):
    """Inject RBAC context (permissions, menu) into each request."""

    def process_request(self, request):
        request.rbac = {}

        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return

        user = request.user

        # Build the navigation menu from accessible modules
        request.rbac['menu'] = build_user_menu(user)

        # Build a flat dict of all permissions for quick lookup
        request.rbac['permissions'] = {}
        if user.is_superuser:
            from .models import Module
            modules = Module.objects.filter(is_active=True)
            for m in modules:
                request.rbac['permissions'][m.key] = ['view', 'create', 'edit', 'delete', 'approve', 'export', 'import', 'assign', 'manage']
        else:
            for role in user.roles.filter(is_active=True):
                for perm in role.permissions.all():
                    key = perm.module.key
                    if key not in request.rbac['permissions']:
                        request.rbac['permissions'][key] = []
                    if perm.permission_type not in request.rbac['permissions'][key]:
                        request.rbac['permissions'][key].append(perm.permission_type)

        # Inject user type helpers
        request.rbac['is_super_admin'] = user.is_super_admin
        request.rbac['is_company_admin'] = user.is_company_admin_user()
        request.rbac['user_type'] = user.user_type
        request.rbac['company_id'] = user.company.id if user.company else None
        request.rbac['company_name'] = user.company.name if user.company else ''
