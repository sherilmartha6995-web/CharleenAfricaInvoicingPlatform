from django.db import models
from django.utils import timezone

# Create your models here.
class Payment(models.Model):
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
        ('REFUNDED', 'Refunded'),
    ]

    invoice = models.ForeignKey('invoices.Invoice', on_delete=models.PROTECT, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    transaction_reference = models.CharField(max_length=100, unique=True)
    payment_date = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True, null=True, help_text="Any extra reconciliation info")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
   

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.invoice.update_payment_status()

    def delete(self, *args, **kwargs):
        invoice = self.invoice
        super().delete(*args, **kwargs)
        invoice.update_payment_status()

class MpesaTransaction(models.Model):
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='mpesa_details')
    merchant_request_id = models.CharField(max_length=100)
    checkout_request_id = models.CharField(max_length=100, unique=True)
    mpesa_receipt_number = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=15)
    result_code = models.IntegerField(null=True, blank=True)
    result_description = models.CharField(max_length=100, null=True, blank=True)
    raw_callback = models.JSONField()
    transactin_date = models.DateTimeField()
    created_at = models.DateTimeField(default=timezone.now)

    def _str_(self):
        return f"Mpesa: {self.mpesa_receipt_number or self.checkout_request_id}"