from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'issues', views.ProjectIssueViewSet)
router.register(r'risks', views.ProjectRiskViewSet)
router.register(r'change-requests', views.ChangeRequestViewSet)
router.register(r'support-tickets', views.SupportTicketViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
