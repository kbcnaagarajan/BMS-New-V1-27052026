from rest_framework import serializers
from .models import ProjectIssue, ProjectRisk, ChangeRequest, SupportTicket


class ProjectIssueSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.project_name', read_only=True)
    assigned_to_name = serializers.SerializerMethodField()
    raised_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ProjectIssue
        fields = '__all__'
        read_only_fields = ['raised_by', 'resolved_by', 'resolved_at', 'created_at', 'updated_at']

    def get_assigned_to_name(self, obj):
        return obj.assigned_to.full_name if obj.assigned_to else ''

    def get_raised_by_name(self, obj):
        return obj.raised_by.full_name if obj.raised_by else ''


class ProjectRiskSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.project_name', read_only=True)
    owner_name = serializers.SerializerMethodField()

    class Meta:
        model = ProjectRisk
        fields = '__all__'
        read_only_fields = ['identified_by', 'created_at', 'updated_at']

    def get_owner_name(self, obj):
        return obj.owner.full_name if obj.owner else ''


class ChangeRequestSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.project_name', read_only=True)

    class Meta:
        model = ChangeRequest
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at']


class SupportTicketSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.project_name', read_only=True)

    class Meta:
        model = SupportTicket
        fields = '__all__'
        read_only_fields = ['submitted_by', 'resolved_by', 'resolved_at', 'created_at', 'updated_at']
