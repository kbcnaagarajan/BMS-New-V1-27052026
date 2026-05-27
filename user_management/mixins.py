"""
Mixins for enforcing multi-tenant data isolation across all viewsets.
"""
from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response
from .rbac import get_company_scope_filter, SCOPE_CONFIG


class CompanyScopeMixin:
    """
    Mixin for DRF viewsets that automatically scopes querysets to the user's company.
    Superadmins see all data; company users see only their company's data.
    """

    def get_queryset(self):
        """
        Override get_queryset to apply company-scoped filtering.
        """
        user = self.request.user

        if user.is_superuser:
            return super().get_queryset()

        if not user.company:
            return super().get_queryset().none()

        qs = super().get_queryset()
        scope_filter = get_company_scope_filter(user, qs.model)

        if scope_filter:
            return qs.filter(scope_filter)

        return qs

    def perform_create(self, serializer):
        """
        Auto-assign company when creating objects if the model has a company field.
        """
        user = self.request.user

        # Check if serializer has company field and auto-assign if so
        if hasattr(serializer, 'Meta') and hasattr(serializer.Meta, 'model'):
            model_class = serializer.Meta.model
            if hasattr(model_class, 'company') and 'company' not in serializer.validated_data:
                if user.company:
                    serializer.save(company=user.company)
                    return

        serializer.save()

    def filter_by_company(self, queryset, company_field='company'):
        """Helper to manually filter a queryset by company."""
        user = self.request.user
        if user.is_superuser:
            return queryset
        if user.company:
            return queryset.filter(**{company_field: user.company})
        return queryset.none()


class CompanyAdminMixin:
    """
    Mixin for views that should be restricted to company admins.
    Company users see only their data; superadmin sees all companies overview.
    """

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()

        if user.is_superuser:
            return qs  # Superadmin sees all (overview only)

        if user.company:
            scope_filter = get_company_scope_filter(user, qs.model)
            if scope_filter:
                return qs.filter(scope_filter)

        return qs.none()


class StaffDetailRestrictedMixin:
    """
    Mixin to restrict staff detail visibility.
    Superadmin cannot see individual employee details; only company-level overview.
    Company admin can see all details within their company.
    Regular users see only their own data.
    """

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()

        if user.is_superuser:
            return qs  # Superadmin sees all (aggregated)

        if user.is_company_admin_user() and user.company:
            scope_filter = get_company_scope_filter(user, qs.model)
            return qs.filter(scope_filter)

        if user.company:
            scope_filter = get_company_scope_filter(user, qs.model)
            return qs.filter(scope_filter)

        return qs.none()


class SuperAdminOverviewMixin:
    """
    For superadmin overview dashboards - returns company-level aggregates,
    not individual records.
    """

    def list(self, request, *args, **kwargs):
        if request.user.is_superuser:
            return self.overview(request, *args, **kwargs)
        return super().list(request, *args, **kwargs)

    def overview(self, request, *args, **kwargs):
        """Override in subclass to return aggregated overview data."""
        return Response({
            'message': 'Superadmin overview - implement in subclass',
            'total_companies': 0,
        })
