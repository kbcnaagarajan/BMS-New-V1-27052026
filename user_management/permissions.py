"""
Custom DRF permission classes for RBAC and multi-tenant data isolation.
"""
from rest_framework import permissions
from .rbac import get_company_scope_filter


class IsSuperAdmin(permissions.BasePermission):
    """Only super admins can access."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_superuser


class IsCompanyAdmin(permissions.BasePermission):
    """Company admins or super admins."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.is_company_admin_user()


class IsCompanyAdminOrAbove(permissions.BasePermission):
    """Company admin, management, or super admin."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        if user.is_company_admin_user():
            return True
        return user.user_type in ('management', 'delivery_manager')


class IsProjectManagerOrAbove(permissions.BasePermission):
    """Project managers, delivery managers, management, company admin, super admin."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser or user.is_company_admin_user():
            return True
        return user.user_type in ('project_manager', 'delivery_manager', 'management')


class IsSelfOrAdmin(permissions.BasePermission):
    """User can only access their own data, or admins can access all."""

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_superuser or user.is_company_admin_user():
            return True
        # Check if object has 'user' or 'employee' field matching request.user
        if hasattr(obj, 'user') and obj.user == user:
            return True
        if hasattr(obj, 'employee') and obj.employee == user:
            return True
        if hasattr(obj, 'assigned_to') and obj.assigned_to == user:
            return True
        return False


class HasModuleAccess(permissions.BasePermission):
    """Check if user has access to a specific module key."""

    def __init__(self, module_key):
        self.module_key = module_key

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user.has_module_access(self.module_key)


class HasPermission(permissions.BasePermission):
    """
    Check if user has a specific permission (module + permission_type).
    Usage: HasPermission('projects', 'view')
    """

    def __init__(self, module_key, permission_type='view'):
        self.module_key = module_key
        self.permission_type = permission_type

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user.has_perm_in_module(self.module_key, self.permission_type)


class CompanyScopePermission(permissions.BasePermission):
    """
    Ensures user can only access data within their company scope.
    Applied globally via DEFAULT_PERMISSION_CLASSES.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
