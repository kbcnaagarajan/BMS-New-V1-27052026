from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Count, Sum, Q, F
from django.utils import timezone
from datetime import timedelta

from user_management.mixins import CompanyScopeMixin
from user_management.rbac import get_company_scope_filter

from client_crm.models import Client
from project_360.models import Project, ProjectTask, ProjectTeamMember
from issues_risks.models import ProjectIssue
from employee_operations.models import Timesheet, Attendance
from billing.models import Invoice, Payment
from user_management.models import User


def scope(user, model):
    return get_company_scope_filter(user, model)


class DashboardViewSet(CompanyScopeMixin, viewsets.ViewSet):

    @action(detail=False, methods=['get'])
    def management(self, request):
        user = request.user

        client_qs = Client.objects.filter(scope(user, Client))
        project_qs = Project.objects.filter(scope(user, Project))
        invoice_qs = Invoice.objects.filter(scope(user, Invoice))
        issue_qs = ProjectIssue.objects.filter(scope(user, ProjectIssue))
        task_qs = ProjectTask.objects.filter(scope(user, ProjectTask))
        timesheet_qs = Timesheet.objects.filter(scope(user, Timesheet))

        total_clients = client_qs.count()
        total_projects = project_qs.count()
        active_projects = project_qs.filter(status__in=['active', 'kickoff_scheduled']).count()
        completed_projects = project_qs.filter(status='completed').count()

        total_invoiced = invoice_qs.aggregate(s=Sum('total_amount'))['s'] or 0
        total_paid = invoice_qs.aggregate(s=Sum('paid_amount'))['s'] or 0

        total_employees = User.objects.filter(
            scope(user, User),
            is_client_user=False, is_active=True
        ).exclude(user_type__in=['super_admin']).count()

        open_issues = issue_qs.filter(status__in=['open', 'in_progress']).count()

        overdue_tasks = task_qs.filter(
            due_date__lt=timezone.now().date(),
            status__in=['new', 'assigned', 'in_progress', 'blocked']
        ).count()

        pending_timesheets = timesheet_qs.filter(status='submitted').count()

        return Response({
            'total_clients': total_clients,
            'total_projects': total_projects,
            'active_projects': active_projects,
            'completed_projects': completed_projects,
            'total_invoices_amount': float(total_invoiced),
            'total_paid_amount': float(total_paid),
            'outstanding_amount': float(total_invoiced - total_paid),
            'total_employees': total_employees,
            'open_issues': open_issues,
            'overdue_tasks': overdue_tasks,
            'pending_timesheets': pending_timesheets,
        })

    @action(detail=False, methods=['get'])
    def revenue_by_client(self, request):
        user = request.user
        data = []
        for client in Client.objects.filter(scope(user, Client), status='active'):
            invoices = Invoice.objects.filter(scope(user, Invoice), client=client)
            total_inv = invoices.aggregate(s=Sum('total_amount'))['s'] or 0
            total_pd = invoices.aggregate(s=Sum('paid_amount'))['s'] or 0
            data.append({
                'client_name': client.name,
                'total_invoiced': float(total_inv),
                'total_paid': float(total_pd),
                'outstanding': float(total_inv - total_pd),
            })
        return Response(data)

    @action(detail=False, methods=['get'])
    def project_health(self, request):
        user = request.user
        projects = Project.objects.filter(
            scope(user, Project)
        ).exclude(status__in=['draft', 'cancelled', 'closed'])

        data = []
        for p in projects:
            data.append({
                'project_name': p.project_name,
                'project_code': p.project_code,
                'client_name': p.client.name,
                'health': p.health,
                'status': p.status,
                'completion': float(p.completion_percentage),
                'project_manager': p.project_manager.full_name if p.project_manager else '',
            })
        return Response(data)

    @action(detail=False, methods=['get'])
    def resource_utilization(self, request):
        user = request.user
        employees = User.objects.filter(
            scope(user, User),
            is_client_user=False, is_active=True
        ).exclude(user_type='super_admin')

        data = []
        for emp in employees:
            assignments = ProjectTeamMember.objects.filter(
                scope(user, ProjectTeamMember),
                user=emp, is_active=True
            )
            total_allocated = assignments.aggregate(
                s=Sum('allocated_hours')
            )['s'] or 0

            total_logged = Timesheet.objects.filter(
                scope(user, Timesheet),
                employee=emp, status='approved'
            ).aggregate(s=Sum('total_hours'))['s'] or 0

            util_pct = 0
            if total_allocated > 0:
                util_pct = round((total_logged / total_allocated) * 100, 2)

            data.append({
                'employee_name': emp.full_name,
                'total_allocated_hours': float(total_allocated),
                'total_logged_hours': float(total_logged),
                'utilization_percentage': util_pct,
                'project_count': assignments.count(),
            })

        return Response(data)

    @action(detail=False, methods=['get'])
    def overdue_tasks(self, request):
        user = request.user
        today = timezone.now().date()
        tasks = ProjectTask.objects.filter(
            scope(user, ProjectTask),
            due_date__lt=today,
            status__in=['new', 'assigned', 'in_progress', 'blocked']
        ).select_related('project', 'assigned_to')[:50]

        data = []
        for t in tasks:
            data.append({
                'id': t.id,
                'title': t.title,
                'project_name': t.project.project_name,
                'assigned_to': t.assigned_to.full_name if t.assigned_to else '',
                'due_date': t.due_date,
                'status': t.status,
                'days_overdue': (today - t.due_date).days,
            })
        return Response(data)

    @action(detail=False, methods=['get'])
    def project_manager(self, request):
        user = request.user
        projects = Project.objects.filter(scope(user, Project), project_manager=user)
        all_tasks = ProjectTask.objects.filter(scope(user, ProjectTask), project__in=projects)

        return Response({
            'total_projects': projects.count(),
            'active_projects': projects.filter(status__in=['active', 'kickoff_scheduled']).count(),
            'completed_projects': projects.filter(status='completed').count(),
            'overdue_tasks': all_tasks.filter(
                due_date__lt=timezone.now().date(),
                status__in=['new', 'assigned', 'in_progress']
            ).count(),
            'pending_timesheets': Timesheet.objects.filter(
                scope(user, Timesheet),
                status='submitted'
            ).count(),
            'open_issues': ProjectIssue.objects.filter(
                scope(user, ProjectIssue),
                project__in=projects,
                status__in=['open', 'in_progress']
            ).count(),
        })

    @action(detail=False, methods=['get'])
    def employee(self, request):
        user = request.user
        tasks = ProjectTask.objects.filter(assigned_to=user)
        today_tasks = tasks.filter(
            created_at__date=timezone.now().date()
        ) | tasks.filter(
            due_date=timezone.now().date()
        )

        recent_timesheets = Timesheet.objects.filter(
            scope(user, Timesheet),
            employee=user
        ).order_by('-week_start_date')[:5]

        today_attendance = Attendance.objects.filter(
            employee=user, date=timezone.now().date()
        ).first()

        return Response({
            'assigned_tasks': tasks.filter(
                status__in=['new', 'assigned', 'in_progress']
            ).count(),
            'today_tasks': today_tasks.distinct().count(),
            'overdue_tasks': tasks.filter(
                due_date__lt=timezone.now().date(),
                status__in=['new', 'assigned', 'in_progress']
            ).count(),
            'pending_timesheets': recent_timesheets.filter(
                status__in=['draft', 'submitted']
            ).count(),
            'is_checked_in': today_attendance.check_in if today_attendance else None,
            'today_status': today_attendance.status if today_attendance else None,
            'my_projects': Project.objects.filter(
                team_members__user=user,
                team_members__is_active=True
            ).distinct().count(),
        })
