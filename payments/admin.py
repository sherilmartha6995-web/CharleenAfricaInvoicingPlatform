from django.contrib import admin
from .models import Payment, MpesaTransaction

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'amount', 'status', 'transaction_reference', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('invoice__invoice_number', 'transaction_reference')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(MpesaTransaction)
class MpesaTransactionAdmin(admin.ModelAdmin):
    list_display = ('checkout_request_id', 'phone_number', 'result_code', 'created_at')
    list_filter = ('result_code',)
    search_fields = ('checkout_request_id', 'phone_number', 'mpesa_receipt_number')
    readonly_fields = ('created_at',)


