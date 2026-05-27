from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'projects', views.ProjectViewSet)
router.register(r'team-members', views.ProjectTeamMemberViewSet)
router.register(r'milestones', views.ProjectMilestoneViewSet)
router.register(r'tasks', views.ProjectTaskViewSet)
router.register(r'task-comments', views.TaskCommentViewSet)
router.register(r'task-attachments', views.TaskAttachmentViewSet)
router.register(r'deliverables', views.ProjectDeliverableViewSet)
router.register(r'status-updates', views.ProjectStatusUpdateViewSet)
router.register(r'documents', views.ProjectDocumentViewSet)
router.register(r'activity-logs', views.ProjectActivityLogViewSet)
router.register(r'closure-checklist', views.ProjectClosureChecklistViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
