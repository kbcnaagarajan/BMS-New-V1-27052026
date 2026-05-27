from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'companies', views.CompanyViewSet)
router.register(r'departments', views.DepartmentViewSet)
router.register(r'designations', views.DesignationViewSet)
router.register(r'modules', views.ModuleViewSet)
router.register(r'permissions', views.PermissionViewSet)
router.register(r'roles', views.RoleViewSet)
router.register(r'users', views.UserViewSet)

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='api_login'),
    path('profile/', views.UserProfileView.as_view(), name='api_profile'),
    path('', include(router.urls)),
]
