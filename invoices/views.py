from playwright.sync_api import sync_playwright
import os
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.http import HttpResponse
from django.http import Http404
from django.template.loader import render_to_string
from django.views.generic import ListView, CreateView
from django.db import transaction
from .utils import email_invoice_to_customer
from django.core.mail import EmailMessage
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Product, Customer, Invoice, InvoiceItem, CreditNote, DebitNote, BusinessProfile 
from django.forms import inlineformset_factory
from .forms import ProductForm, CustomerForm, InvoiceForm, InvoiceItemFormSet, CreditNoteForm, DebitNoteForm, BusinessProfileForm

class ProductListView(ListView):
    model = Product
    template_name = 'invoices/product_list.html'
    context_object_name = 'products'

    def get_queryset(self):
        active_business_id = self.request.session.get('active_business_id')
        return Product.objects.filter(business_id=active_business_id)

class ProductCreateView(CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'invoices/product_form.html'
    success_url = reverse_lazy('product_list')

    def form_valid(self, form):
        active_business_id = self.request.session.get('active_business_id')
        
        if not active_business_id:
            print("ERROR: No active_business_id in session!")
            return self.form_invalid(form)
            
        form.instance.business_id = active_business_id
        return super().form_valid(form)

class CustomerListView(ListView):
    model = Customer
    template_name = 'invoices/customer_list.html'
    context_object_name = 'customers'

    def get_queryset(self):
        active_business_id = self.request.session.get('active_business_id')
        return Customer.objects.filter(business_id=active_business_id)

class CustomerCreateView(CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'invoices/customer_form.html'
    success_url = reverse_lazy('customer_list')

    def form_valid(self, form):
        active_business_id = self.request.session.get('active_business_id')
        form.instance.business_id = active_business_id
        return super().form_valid(form)
    
class CustomerUpdateView(UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'invoices/customer_form.html'
    success_url = reverse_lazy('customer_list')

class CustomerDeleteView(DeleteView):
    model = Customer
    template_name = 'invoices/customer_confirm_delete.html'
    success_url = reverse_lazy('customer_list')    
    
class InvoiceListView(ListView):
    model = Invoice
    template_name = 'invoices/invoice_list.html'
    context_object_name = 'invoices'
    ordering = ['-created_at']

    def get_queryset(self):
        active_business_id = self.request.session.get('active_business_id')
        
        return Invoice.objects.filter(business_id=active_business_id)

def invoice_create_view(request):
    active_business_id = request.session.get('active_business_id')
    
    if not active_business_id:
        return redirect('business_list') 

    if request.method == 'POST':
        form = InvoiceForm(request.POST, business_id=active_business_id)
        formset = InvoiceItemFormSet(request.POST, request.FILES, instance=form.instance, form_kwargs={'business_id': active_business_id})
        
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    invoice = form.save(commit=False)
                    invoice.business_id = active_business_id
                    invoice.save()
                    
                    formset.instance = invoice
                    formset.save()
                    invoice.calculate_totals()

                return redirect('invoice_list')
            except Exception as e:
                print(f"Database write exception: {str(e)}")
    else:
        form = InvoiceForm(business_id=active_business_id)
        formset = InvoiceItemFormSet(instance=form.instance, form_kwargs={'business_id': active_business_id})

    products = Product.objects.filter(business_id=active_business_id)
    product_prices = {p.id: float(p.price) for p in products}

    context = {
        'form': form,
        'formset': formset,
        'product_prices_json': json.dumps(product_prices),
    }
    return render(request, 'invoices/invoice_form.html', context)

def invoice_detail_view(request, invoice_uuid):
    active_business_id = request.session.get('active_business_id')
    
    invoice = get_object_or_404(Invoice, invoice_uuid=invoice_uuid, business_id=active_business_id)
    
    if request.method == 'POST':
        invoice_form = InvoiceForm(request.POST, request.FILES, instance=invoice, business_id=active_business_id)
        
        formset = InvoiceItemFormSet(
            request.POST, 
            request.FILES, 
            instance=invoice, 
            prefix='form',
            form_kwargs={'business_id': active_business_id}
        )
        
        if invoice_form.is_valid() and formset.is_valid():
            invoice_form.save()
            formset.instance = invoice
            formset.save()
            return redirect('invoice_detail', invoice_uuid=invoice.invoice_uuid)
            
    else:
        invoice_form = InvoiceForm(instance=invoice, business_id=active_business_id)
        
        formset = InvoiceItemFormSet(
            instance=invoice, 
            prefix='form',
            form_kwargs={'business_id': active_business_id}
        )
        
    context = {
        'invoice': invoice,
        'invoice_form': invoice_form,
        'formset': formset,
    }
    return render(request, 'invoices/invoice_detail.html', context)
                  
def compile_pdf_with_playwright(html_content):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        page.set_content(html_content, wait_until="networkidle")
        
        pdf_buffer = page.pdf(
            format="A4",
            margin={"top": "0px", "right": "0px", "bottom": "0px", "left": "0px"},
            print_background=True
        )
        browser.close()
        return pdf_buffer

def invoice_pdf_view(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    line_items = invoice.items.all()

    context = {
        'invoice': invoice,
        'line_items': line_items,
    }

    html_string = render_to_string('invoices/invoice_pdf_template.html', context)
    pdf_data = compile_pdf_with_playwright(html_string)

    response = HttpResponse(pdf_data, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Invoice_{invoice.id:04d}.pdf"'
    return response

def send_invoice_email_view(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    if not invoice.customer or not invoice.customer.email:
        messages.error(request, "Cannot dispatch email: Customer profile has no valid registered email.")
        return redirect('invoice_detail', invoice_uuid=invoice.invoice_uuid)

    line_items = invoice.items.all()

    context = {
        'invoice': invoice,
        'line_items': line_items,
    }

    html_string = render_to_string('invoices/invoice_pdf_template.html', context)
    pdf_data = compile_pdf_with_playwright(html_string)

    try:
        subject = f"Official Invoice #{invoice.id:04d} - Charleen Africa Invoicing"
        email_body = f"Dear {invoice.customer.name},\n\nPlease find attached your official invoice statement for services rendered.\n\nWarm regards,\nCharleen Africa Invoicing Team"
        
        email = EmailMessage(
            subject=subject,
            body=email_body,
            from_email='sherilmartha2004@gmail.com',
            to=[invoice.customer.email]
        )
        
        email.attach(f"Invoice_{invoice.id:04d}.pdf", pdf_data, 'application/pdf')
        email.send()
        
        messages.success(request, f"Official PDF Invoice successfully compiled and dispatched to {invoice.customer.email}!")
        
    except Exception as e:
        messages.error(request, f"Encountered systemic fault routing email dispatch: {str(e)}")

    return redirect('invoice_detail', invoice_uuid=invoice.invoice_uuid)

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully! You can now log in.')
            return redirect('login')
    else:
        form = UserCreationForm()
        
    context = {'form': form}
    return render(request, 'invoices/register.html', context)

def credit_note_list_view(request):
    credit_notes = CreditNote.objects.all().order_by('-created_at')
    context = {'credit_notes': credit_notes}
    return render(request, 'invoices/credit_note_list.html', context)

def debit_note_list_view(request):
    debit_notes = DebitNote.objects.all().order_by('-created_at')
    context = {'debit_notes': debit_notes}
    return render(request, 'invoices/debit_note_list.html', context)


def create_credit_note(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    if request.method == 'POST':
        form = CreditNoteForm(request.POST)
        if form.is_valid():
            credit_note = form.save(commit=False)
            credit_note.invoice = invoice
            credit_note.save()
            return redirect('invoice_detail', pk=invoice.id)
    else:
        form = CreditNoteForm(initial={
            'subtotal': invoice.subtotal, 
            'tax_amount': invoice.tax_amount, 
            'total_amount': invoice.total_amount
        })
        
    context = {'form': form, 'invoice': invoice, 'title': 'Create Credit Note'}
    return render(request, 'invoices/note_form.html', context)

def create_debit_note(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    if request.method == 'POST':
        form = DebitNoteForm(request.POST)
        if form.is_valid():
            debit_note = form.save(commit=False)
            debit_note.invoice = invoice
            debit_note.save()
            return redirect('invoice_detail', pk=invoice.id)
    else:
        form = DebitNoteForm(initial={
            'subtotal': invoice.subtotal, 
            'tax_amount': invoice.tax_amount, 
            'total_amount': invoice.total_amount
        })
        
    context = {'form': form, 'invoice': invoice, 'title': 'Create Debit Note'}
    return render(request, 'invoices/note_form.html', context)

def register_business_view(request):
    if request.method == 'POST':
        form = BusinessProfileForm(request.POST)
        if form.is_valid():
            business = form.save(commit=False)
            business.owner = request.user 
            business.save()
            return redirect('business_list')
    else:
        form = BusinessProfileForm()
    return render(request, 'invoices/register_business.html', {'form': form})



def set_active_business(request, business_id):
    business = get_object_or_404(BusinessProfile, id=business_id, owner=request.user)
    
    request.session['active_business_id'] = business.id
    
    return redirect('invoice_list') 

def get_active_business(request):
    business_id = request.session.get('active_business_id')
    if business_id:
        try:
            return BusinessProfile.objects.get(id=business_id, owner=request.user)
        except BusinessProfile.DoesNotExist:
            pass
    
    first_business = BusinessProfile.objects.filter(owner=request.user).first()
    if first_business:
        request.session['active_business_id'] = first_business.id
        return first_business
    
    return None

def business_list_view(request):
    businesses = BusinessProfile.objects.filter(owner=request.user)
    return render(request, 'invoices/business_list.html', {'businesses': businesses})

def home_view(request):
    return render(request, 'invoices/home.html')