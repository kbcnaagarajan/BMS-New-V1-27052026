import django_filters
from .models import Project


class ProjectFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(lookup_expr='exact')
    status_in = django_filters.BaseInFilter(field_name='status', lookup_expr='in')
    health = django_filters.CharFilter(lookup_expr='exact')
    priority = django_filters.CharFilter(lookup_expr='exact')
    client = django_filters.NumberFilter(field_name='client__id')
    project_manager = django_filters.NumberFilter(field_name='project_manager__id')
    delivery_manager = django_filters.NumberFilter(field_name='delivery_manager__id')

    class Meta:
        model = Project
        fields = ['status', 'health', 'priority', 'client', 'project_manager', 'billing_type']
