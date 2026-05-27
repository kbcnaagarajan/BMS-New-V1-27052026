from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="KarthikAi-OMS API",
        default_version='v1',
        description="KarthikAi Operations Management System - Client CRM & Project Delivery Platform",
        contact=openapi.Contact(email="admin@karthikai.com"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # API Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # JWT Authentication
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # App APIs
    path('api/auth/', include('user_management.urls')),
    path('api/crm/', include('client_crm.urls')),
    path('api/projects/', include('project_360.urls')),
    path('api/operations/', include('employee_operations.urls')),
    path('api/issues/', include('issues_risks.urls')),
    path('api/billing/', include('billing.urls')),
    path('api/meetings/', include('meetings_documents.urls')),
    path('api/portal/', include('client_portal.urls')),
    path('api/reports/', include('reports_dashboards.urls')),

    # Frontend Pages
    path('', include('user_management.frontend_urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else settings.STATIC_ROOT)
