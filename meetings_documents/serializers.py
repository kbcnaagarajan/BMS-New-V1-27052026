from rest_framework import serializers
from .models import Meeting, MeetingActionItem, Document, Notification


class MeetingActionItemSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.SerializerMethodField()

    class Meta:
        model = MeetingActionItem
        fields = '__all__'

    def get_assigned_to_name(self, obj):
        return obj.assigned_to.full_name if obj.assigned_to else ''


class MeetingSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.project_name', read_only=True)
    organizer_name = serializers.SerializerMethodField()
    action_items = MeetingActionItemSerializer(many=True, read_only=True)
    attendee_names = serializers.SerializerMethodField()

    class Meta:
        model = Meeting
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def get_organizer_name(self, obj):
        return obj.organizer.full_name if obj.organizer else ''

    def get_attendee_names(self, obj):
        return [u.full_name for u in obj.attendees.all()]


class DocumentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = '__all__'
        read_only_fields = ['uploaded_by', 'created_at', 'updated_at']

    def get_uploaded_by_name(self, obj):
        return obj.uploaded_by.full_name if obj.uploaded_by else ''


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ['created_at']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.pop('user', None)  # Hide other user's notifications
        return data
