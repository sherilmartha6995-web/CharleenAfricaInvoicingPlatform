import uuid
from django.db import models
from django.utils import timezone
from django.db.models import Sum
from django.conf import settings

class BusinessProfile(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='businesses')
    business_name = models.CharField(max_length=100)
    kra_pin = models.CharField(max_length=11,unique=True)
    is_vat_registered = models.BooleanField(default=True, verbose_name="VAT Registered")
    address = models.TextField()
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    created_at = models.DateTimeField(default=timezone.now) 

    def _str_(self):
        return self.business_name

class Customer(models.Model):
    business = models.ForeignKey(BusinessProfile, on_delete=models.PROTECT, blank=True, null=True, related_name='customers')
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    kra_pin = models.CharField(max_length=11, blank=True, null=True, unique=True)
    address = models.TextField(blank=True, null=True) 

    def __str__(self):
        return self.name

class Product(models.Model):
    PRODUCT_TYPE_CHOICES = [
        ('GOODS', 'goods'),
        ('SERVICE', 'Service'),
    ]

    name = models.CharField(max_length=100)
    business =  models.ForeignKey(BusinessProfile,  on_delete=models.PROTECT, blank=True, null=True, related_name='products')
    sku = models.CharField(max_length=100, unique=True, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    product_type = models.CharField(max_length=10, choices=PRODUCT_TYPE_CHOICES, default='GOODS')
    stock_quantity = models.IntegerField(default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=16.0)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('business', 'sku') 

    def __str__(self):
        return f"{self.name} ({self.sku if self.sku else 'No SKU'})"

class Invoice(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('UNPAID', 'Unpaid'),
         ('PARTIAL', 'partial'),
        ('PAID', 'Fully Paid'),
    ]
    
    business = models.ForeignKey('BusinessProfile', on_delete=models.PROTECT,  related_name='invoices', null=True, blank=True)
    invoice_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    invoice_number = models.CharField(max_length=50, unique=True, blank=True)
    customer = models.ForeignKey('Customer', on_delete=models.PROTECT, related_name='invoices')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    issue_date = models.DateField(default=timezone.now)
    due_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='UNPAID')
    kra_submission_id = models.CharField(max_length=100, blank=True, null=True)
    email_sent = models.BooleanField(default=False)
    printed = models.BooleanField(default=False)

    def __str__(self):
        customer_name = self.customer.name if hasattr(self.customer, 'name') else "Unknown Customer"
        return f"{self.invoice_number or 'No Number'} - {customer_name}"

    def calculate_totals(self):
        totals = self.items.aggregate(
            sum_subtotal=models.Sum('amount')
        )
        self.subtotal = totals['sum_subtotal'] or 0.0
        
        total_tax = 0.0
        for item in self.items.all():
            total_tax += float(item.amount) * (float(item.tax_rate) / 100.0)
            
        self.tax_amount = total_tax
        self.total_amount = float(self.subtotal) + total_tax
        
        super().save(update_fields=['subtotal', 'tax_amount', 'total_amount'])

    def update_payment_status(self):
        total_paid = self.payments.filter(status='COMPLETED').aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
    
        if total_paid >= self.total_amount:
           self.payment_status = 'PAID'
        elif total_paid > 0:
          self.payment_status = 'PARTIAL'
        else:
          self.payment_status = 'UNPAID'
    
        self.save(update_fields=['payment_status'])

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            last_invoice = Invoice.objects.order_by('id').last()
            prefix = "INV-2026-"
            
            if last_invoice and last_invoice.invoice_number:
                try:
                    last_number_str = last_invoice.invoice_number.split('-')[-1]
                    next_number = int(last_number_str) + 1
                except (ValueError, IndexError):
                    next_number = 1
            else:
                next_number = 1
                
            self.invoice_number = f"{prefix}{next_number:06d}"
            
        super().save(*args, **kwargs)


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name='items')
    product = models.ForeignKey('Product', on_delete=models.PROTECT, related_name='invoice_items')
    quantity = models.IntegerField(default=1)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=16.0)
    amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True)

    def __str__(self):
        return f"{self.product} (x{self.quantity})"

    def save(self, *args, **kwargs):
        if not self.amount and self.product:
            self.amount = self.quantity * self.product.price
            
        super().save(*args, **kwargs)
        self.invoice.calculate_totals()

    def delete(self, *args, **kwargs):
        parent_invoice = self.invoice
        super().delete(*args, **kwargs)
        parent_invoice.calculate_totals()
    
class CreditNote(models.Model):
    credit_note_number = models.CharField(max_length=50, unique=True, blank=True)
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name='credit_notes')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    reason = models.TextField()
    kra_submission_id = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        if not self.credit_note_number:
            last_cn = CreditNote.objects.order_by('id').last()
            next_num = (int(last_cn.credit_note_number.split('-')[-1]) + 1) if last_cn else 1
            self.credit_note_number = f"CN-2026-{next_num:06d}"
        super().save(*args, **kwargs)

class DebitNote(models.Model):
    debit_note_number = models.CharField(max_length=50, unique=True, blank=True)
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name='debit_notes')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    reason = models.TextField()
    kra_submission_id = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        if not self.debit_note_number:
            last_dn = DebitNote.objects.order_by('id').last()
            next_num = (int(last_dn.debit_note_number.split('-')[-1]) + 1) if last_dn else 1
            self.debit_note_number = f"DN-2026-{next_num:06d}"
        super().save(*args, **kwargs)

