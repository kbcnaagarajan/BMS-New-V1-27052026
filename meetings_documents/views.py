from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from user_management.mixins import CompanyScopeMixin
from .models import Meeting, MeetingActionItem, Document, Notification
from .serializers import (
    MeetingSerializer, MeetingActionItemSerializer,
    DocumentSerializer, NotificationSerializer
)


class MeetingViewSet(CompanyScopeMixin, viewsets.ModelViewSet):
    queryset = Meeting.objects.all()
    serializer_class = MeetingSerializer
    filterset_fields = ['project', 'meeting_type', 'status', 'meeting_date']
    search_fields = ['title', 'project__project_name']

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        meeting = self.get_object()
        meeting.status = 'completed'
        meeting.minutes = request.data.get('minutes', meeting.minutes)
        meeting.save()
        return Response(MeetingSerializer(meeting).data)


class MeetingActionItemViewSet(CompanyScopeMixin, viewsets.ModelViewSet):
    queryset = MeetingActionItem.objects.all()
    serializer_class = MeetingActionItemSerializer
    filterset_fields = ['meeting', 'assigned_to', 'status']

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        item = self.get_object()
        item.status = 'completed'
        item.completed_at = timezone.now()
        item.save()
        return Response(MeetingActionItemSerializer(item).data)


class DocumentViewSet(CompanyScopeMixin, viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    filterset_fields = ['project', 'client', 'document_type', 'visibility']
    search_fields = ['title', 'description']

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


class NotificationViewSet(CompanyScopeMixin, viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    filterset_fields = ['notification_type', 'is_read']

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({'unread_count': count})

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notif = self.get_object()
        notif.is_read = True
        notif.save()
        return Response(NotificationSerializer(notif).data)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'status': 'all marked as read'})
