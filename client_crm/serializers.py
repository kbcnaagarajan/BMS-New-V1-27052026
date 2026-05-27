from rest_framework import serializers
from .models import Client, ClientContact, ClientLocation, ClientContract, ClientNote, ClientCommunicationLog


class ClientContactSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = ClientContact
        fields = '__all__'

    def get_full_name(self, obj):
        return f'{obj.first_name} {obj.last_name}'.strip()


class ClientLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientLocation
        fields = '__all__'


class ClientContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientContract
        fields = '__all__'


class ClientNoteSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ClientNote
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at']

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.full_name
        return ''


class ClientCommunicationLogSerializer(serializers.ModelSerializer):
    communicated_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ClientCommunicationLog
        fields = '__all__'
        read_only_fields = ['communicated_by', 'communicated_at']

    def get_communicated_by_name(self, obj):
        if obj.communicated_by:
            return obj.communicated_by.full_name
        return ''


class ClientListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['id', 'client_code', 'name', 'client_type', 'industry', 'status',
                  'email', 'phone', 'country', 'city', 'assigned_account_manager',
                  'contract_start_date', 'contract_end_date', 'created_at']


class ClientDetailSerializer(serializers.ModelSerializer):
    contacts = ClientContactSerializer(many=True, read_only=True)
    locations = ClientLocationSerializer(many=True, read_only=True)
    contracts = ClientContractSerializer(many=True, read_only=True)
    client_notes = ClientNoteSerializer(many=True, read_only=True, source='client_notes')
    communications = ClientCommunicationLogSerializer(many=True, read_only=True)
    assigned_manager_name = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = '__all__'

    def get_assigned_manager_name(self, obj):
        if obj.assigned_account_manager:
            return obj.assigned_account_manager.full_name
        return ''

    def get_company_name(self, obj):
        if obj.company:
            return obj.company.name
        return ''
