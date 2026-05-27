from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'clients', views.ClientViewSet)
router.register(r'contacts', views.ClientContactViewSet)
router.register(r'locations', views.ClientLocationViewSet)
router.register(r'contracts', views.ClientContractViewSet)
router.register(r'notes', views.ClientNoteViewSet)
router.register(r'communications', views.ClientCommunicationLogViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
