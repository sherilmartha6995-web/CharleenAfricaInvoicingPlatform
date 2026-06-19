from django.contrib import admin
from .models import Customer, Product, Invoice, InvoiceItem, CreditNote, DebitNote, Payment

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    fields = ['product', 'quantity', 'tax_rate', 'amount']

admin.site.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'customer', 'total_amount', 'status', 'payment_status', 'issue_date']
    list_filter = ['status', 'payment_status', 'issue_date']
    search_fields = ['invoice_number', 'customer__name']
    inlines = [InvoiceItemInline]
    readonly_fields = ['invoice_number', 'subtotal', 'tax_amount', 'total_amount']

admin.site.register(CreditNote)
class CreditNoteAdmin(admin.ModelAdmin):
    list_display = ['credit_note_number', 'invoice', 'total_amount', 'created_at']
    readonly_fields = ['credit_note_number', 'subtotal', 'tax_amount', 'total_amount']

admin.site.register(DebitNote)
class DebitNoteAdmin(admin.ModelAdmin):
    list_display = ['debit_note_number', 'invoice', 'total_amount', 'created_at']
    readonly_fields = ['debit_note_number', 'subtotal', 'tax_amount', 'total_amount']

admin.site.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['transaction_reference', 'invoice', 'amount_paid', 'payment_method', 'payment_date']
    search_fields = ['transaction_reference', 'invoice__invoice_number']

admin.site.register(Customer)
admin.site.register(Product)
