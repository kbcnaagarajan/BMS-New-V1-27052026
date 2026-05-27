from django.contrib import admin
from .models import Client, ClientContact, ClientLocation, ClientContract, ClientNote, ClientCommunicationLog


class ClientContactInline(admin.TabularInline):
    model = ClientContact
    extra = 1


class ClientLocationInline(admin.TabularInline):
    model = ClientLocation
    extra = 1


class ClientContractInline(admin.TabularInline):
    model = ClientContract
    extra = 1


class ClientNoteInline(admin.TabularInline):
    model = ClientNote
    extra = 1


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['company', 'client_code', 'name', 'client_type', 'industry', 'status', 'email', 'phone', 'assigned_account_manager']
    list_filter = ['company', 'status', 'client_type', 'industry', 'country']
    search_fields = ['name', 'client_code', 'email', 'phone']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ClientContactInline, ClientLocationInline, ClientContractInline, ClientNoteInline]
    fieldsets = (
        ('Basic Information', {'fields': ('client_code', 'name', 'client_type', 'industry', 'status', 'logo')}),
        ('Registration', {'fields': ('registration_number', 'tax_number', 'website', 'phone', 'email')}),
        ('Address', {'fields': ('address_line1', 'address_line2', 'country', 'state', 'city', 'pincode')}),
        ('Contract & Terms', {'fields': ('contract_start_date', 'contract_end_date', 'billing_terms', 'sla_terms', 'support_terms')}),
        ('Assignment', {'fields': ('assigned_account_manager',)}),
        ('Notes', {'fields': ('notes',)}),
        ('Audit', {'fields': ('created_by', 'created_at', 'updated_at')}),
    )


@admin.register(ClientContact)
class ClientContactAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'client', 'email', 'phone', 'is_primary', 'can_login']
    list_filter = ['is_primary', 'can_login']
    search_fields = ['first_name', 'last_name', 'email', 'client__name']


@admin.register(ClientLocation)
class ClientLocationAdmin(admin.ModelAdmin):
    list_display = ['location_name', 'client', 'city', 'country', 'is_headquarters']
    list_filter = ['country', 'is_headquarters']


@admin.register(ClientContract)
class ClientContractAdmin(admin.ModelAdmin):
    list_display = ['contract_title', 'client', 'start_date', 'end_date', 'value', 'status']
    list_filter = ['status']
    search_fields = ['contract_title', 'client__name']


@admin.register(ClientCommunicationLog)
class ClientCommunicationLogAdmin(admin.ModelAdmin):
    list_display = ['subject', 'client', 'communication_type', 'direction', 'contact_person', 'communicated_at']
    list_filter = ['communication_type', 'direction', 'communicated_at']
    search_fields = ['subject', 'client__name']
