from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'attendance', views.AttendanceViewSet)
router.register(r'leave-policies', views.LeavePolicyViewSet)
router.register(r'leave-balances', views.LeaveBalanceViewSet)
router.register(r'leave-requests', views.LeaveRequestViewSet)
router.register(r'wfh-requests', views.WFHRequestViewSet)
router.register(r'timesheets', views.TimesheetViewSet)
router.register(r'timesheet-entries', views.TimesheetEntryViewSet)
router.register(r'expense-categories', views.ExpenseCategoryViewSet)
router.register(r'expenses', views.ExpenseViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
