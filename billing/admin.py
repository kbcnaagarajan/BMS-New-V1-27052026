from django.contrib import admin
from .models import BillingMilestone, Invoice, Payment


@admin.register(BillingMilestone)
class BillingMilestoneAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'amount', 'due_date', 'status']
    list_filter = ['status']
    search_fields = ['title', 'project__project_name']


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 1
    readonly_fields = ['created_at']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'client', 'project', 'invoice_date', 'due_date',
                    'total_amount', 'paid_amount', 'balance_amount', 'status']
    list_filter = ['status', 'invoice_date']
    search_fields = ['invoice_number', 'client__name', 'project__project_name']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [PaymentInline]
    fieldsets = (
        ('Invoice Info', {'fields': ('invoice_number', 'project', 'client', 'billing_milestone')}),
        ('Dates', {'fields': ('invoice_date', 'due_date')}),
        ('Amounts', {'fields': ('amount', 'tax_amount', 'total_amount', 'paid_amount', 'balance_amount', 'currency')}),
        ('Status', {'fields': ('status',)}),
        ('Additional', {'fields': ('notes', 'invoice_document')}),
        ('Audit', {'fields': ('created_by', 'created_at', 'updated_at')}),
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'client', 'amount', 'payment_date', 'payment_mode', 'reference_number']
    list_filter = ['payment_mode', 'payment_date']
    search_fields = ['reference_number', 'invoice__invoice_number', 'client__name']
