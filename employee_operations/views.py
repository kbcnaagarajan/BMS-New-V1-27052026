from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from user_management.mixins import CompanyScopeMixin
from django.db.models import Sum
from .models import (
    Attendance, LeavePolicy, LeaveBalance, LeaveRequest, WFHRequest,
    Timesheet, TimesheetEntry, ExpenseCategory, Expense
)
from .serializers import (
    AttendanceSerializer, LeavePolicySerializer, LeaveBalanceSerializer,
    LeaveRequestSerializer, WFHRequestSerializer, TimesheetSerializer,
    TimesheetEntrySerializer, TimesheetSubmissionSerializer, ExpenseCategorySerializer,
    ExpenseSerializer
)


class AttendanceViewSet(CompanyScopeMixin, viewsets.ModelViewSet):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    filterset_fields = ['employee', 'date', 'status']
    search_fields = ['employee__email', 'employee__first_name']

    @action(detail=False, methods=['post'])
    def check_in(self, request):
        today = timezone.now().date()
        att, created = Attendance.objects.get_or_create(
            employee=request.user,
            date=today,
            defaults={
                'check_in': timezone.now(),
                'status': 'present',
                'marked_by': request.user,
            }
        )
        if not created:
            return Response({'error': 'Already checked in today'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(AttendanceSerializer(att).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def check_out(self, request):
        today = timezone.now().date()
        try:
            att = Attendance.objects.get(employee=request.user, date=today)
            if att.check_out:
                return Response({'error': 'Already checked out today'}, status=status.HTTP_400_BAD_REQUEST)
            att.check_out = timezone.now()
            if att.check_in:
                delta = att.check_out - att.check_in
                att.total_hours = round(delta.total_seconds() / 3600, 2)
            att.save()
            return Response(AttendanceSerializer(att).data)
        except Attendance.DoesNotExist:
            return Response({'error': 'No check-in found for today'}, status=status.HTTP_400_BAD_REQUEST)


class LeavePolicyViewSet(CompanyScopeMixin, viewsets.ModelViewSet):
    queryset = LeavePolicy.objects.all()
    serializer_class = LeavePolicySerializer
    filterset_fields = ['leave_type', 'is_active']


class LeaveBalanceViewSet(CompanyScopeMixin, viewsets.ModelViewSet):
    queryset = LeaveBalance.objects.all()
    serializer_class = LeaveBalanceSerializer
    filterset_fields = ['employee', 'leave_policy', 'year']


class LeaveRequestViewSet(CompanyScopeMixin, viewsets.ModelViewSet):
    queryset = LeaveRequest.objects.all()
    serializer_class = LeaveRequestSerializer
    filterset_fields = ['employee', 'status', 'leave_policy']

    def perform_create(self, serializer):
        serializer.save(employee=self.request.user)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        leave = self.get_object()
        leave.status = 'approved'
        leave.approved_by = request.user
        leave.approved_at = timezone.now()
        leave.save()
        return Response(LeaveRequestSerializer(leave).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        leave = self.get_object()
        leave.status = 'rejected'
        leave.approved_by = request.user
        leave.rejection_reason = request.data.get('reason', '')
        leave.save()
        return Response(LeaveRequestSerializer(leave).data)


class WFHRequestViewSet(CompanyScopeMixin, viewsets.ModelViewSet):
    queryset = WFHRequest.objects.all()
    serializer_class = WFHRequestSerializer
    filterset_fields = ['employee', 'status', 'date']

    def perform_create(self, serializer):
        serializer.save(employee=self.request.user)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        wfh = self.get_object()
        wfh.status = 'approved'
        wfh.approved_by = request.user
        wfh.approved_at = timezone.now()
        wfh.save()
        return Response(WFHRequestSerializer(wfh).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        wfh = self.get_object()
        wfh.status = 'rejected'
        wfh.approved_by = request.user
        wfh.rejected_reason = request.data.get('reason', '')
        wfh.save()
        return Response(WFHRequestSerializer(wfh).data)


class TimesheetViewSet(CompanyScopeMixin, viewsets.ModelViewSet):
    queryset = Timesheet.objects.all()
    serializer_class = TimesheetSerializer
    filterset_fields = ['employee', 'status', 'week_start_date']
    search_fields = ['employee__email']

    def perform_create(self, serializer):
        serializer.save(employee=self.request.user)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        ts = self.get_object()
        ts.status = 'submitted'
        ts.save()
        return Response(TimesheetSerializer(ts).data)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        ts = self.get_object()
        ts.status = 'approved'
        ts.approved_by = request.user
        ts.approved_at = timezone.now()
        ts.save()
        return Response(TimesheetSerializer(ts).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        ts = self.get_object()
        ts.status = 'rejected'
        ts.approved_by = request.user
        ts.rejection_reason = request.data.get('reason', '')
        ts.save()
        return Response(TimesheetSerializer(ts).data)

    @action(detail=False, methods=['get'])
    def my_pending(self, request):
        ts = Timesheet.objects.filter(
            employee=request.user,
            status__in=['draft', 'submitted']
        )
        serializer = TimesheetSerializer(ts, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def pending_approval(self, request):
        ts = Timesheet.objects.filter(status='submitted')
        serializer = TimesheetSerializer(ts, many=True)
        return Response(serializer.data)


class TimesheetEntryViewSet(CompanyScopeMixin, viewsets.ModelViewSet):
    queryset = TimesheetEntry.objects.all()
    serializer_class = TimesheetEntrySerializer
    filterset_fields = ['timesheet', 'project', 'date', 'is_billable']


class ExpenseCategoryViewSet(CompanyScopeMixin, viewsets.ModelViewSet):
    queryset = ExpenseCategory.objects.all()
    serializer_class = ExpenseCategorySerializer
    filterset_fields = ['is_active']


class ExpenseViewSet(CompanyScopeMixin, viewsets.ModelViewSet):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    filterset_fields = ['employee', 'project', 'category', 'status']

    def perform_create(self, serializer):
        serializer.save(employee=self.request.user)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        exp = self.get_object()
        exp.status = 'approved'
        exp.approved_by = request.user
        exp.approved_at = timezone.now()
        exp.save()
        return Response(ExpenseSerializer(exp).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        exp = self.get_object()
        exp.status = 'rejected'
        exp.approved_by = request.user
        exp.notes = request.data.get('reason', '')
        exp.save()
        return Response(ExpenseSerializer(exp).data)
