from django import forms
from django.forms.widgets import Select
from .models import Product, Customer, Invoice, InvoiceItem, CreditNote, DebitNote, BusinessProfile, ProofOfDelivery


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'sku', 'description', 'price', 'product_type', 'stock_quantity', 'tax_rate']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'sku': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3,}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'product_type': forms.Select(attrs={'class': 'form-control'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'tax_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'email', 'phone_number', 'kra_pin', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'kra_pin': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3,}),
        }

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['customer', 'issue_date', 'due_date', 'status', 'payment_status']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'issue_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'payment_status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        business_id = kwargs.pop('business_id', None)
        super().__init__(*args, **kwargs)
        
        if business_id:
            self.fields['customer'].queryset = Customer.objects.filter(business_id=business_id)

class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ['product', 'quantity', 'amount', 'tax_rate']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control product-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control quantity-input', 'min': '1', 'step': '1'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control amount-input', 'readonly': 'readonly'}),
            'tax_rate': forms.NumberInput(attrs={'class': 'form-control tax-rate-input', 'readonly': 'readonly'}),
        }

    def __init__(self, *args, **kwargs):
        business_id = kwargs.pop('business_id', None)
        super().__init__(*args, **kwargs)
        if business_id:
            self.fields['product'].queryset = Product.objects.filter(business_id=business_id)
            self.fields['product'].label_from_instance = ( lambda obj: f"{obj.name} - KES {obj.price:,.2f}")

InvoiceItemFormSet = forms.inlineformset_factory(
    Invoice,
    InvoiceItem,
    form=InvoiceItemForm,
    fields=['product', 'quantity', 'amount', 'tax_rate'],
    extra=1,
    can_delete=True,
)

class ProductSelectWidget(Select):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        if value not in [None, ''] and hasattr(self.choices, 'queryset'):
            try:
                product_obj = self.choices.queryset.get(pk=value)
                if product_obj and hasattr(product_obj, 'price'):
                    option['attrs']['data-price'] = str(float(product_obj.price))
            except (ValueError, TypeError, self.choices.queryset.model.DoesNotExist):
                pass
                
        return option
    
class CreditNoteForm(forms.ModelForm):
    class Meta:
        model = CreditNote
        fields = ['reason', 'subtotal', 'tax_amount', 'total_amount']
        widgets = {
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Reason for issuing the credit note...'}),
            'subtotal': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class DebitNoteForm(forms.ModelForm):
    class Meta:
        model = DebitNote
        fields = ['reason', 'subtotal', 'tax_amount', 'total_amount']
        widgets = {
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'subtotal': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class BusinessProfileForm(forms.ModelForm):
    class Meta:
        model = BusinessProfile
        fields = [
            'business_name', 
            'kra_pin', 
            'is_vat_registered', 
            'address', 
            'email', 
            'phone_number'
        ]

class PODForm(forms.ModelForm):
    class Meta:
        model = ProofOfDelivery
        fields = [
            'status', 'confirmation_method', 'recipient_email', 
            'recipient_phone', 'delivered_by', 
            'document', 'received_by', 'notes'
        ]
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'confirmation_method': forms.Select(attrs={'class': 'form-control'}),
            'recipient_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'recipient_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'delivered_by': forms.TextInput(attrs={'class': 'form-control'}),
            'received_by': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
