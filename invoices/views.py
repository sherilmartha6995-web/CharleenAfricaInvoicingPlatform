from playwright.sync_api import sync_playwright
import os
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
from .models import Product, Customer, Invoice, InvoiceItem
from django.forms import inlineformset_factory
from .forms import ProductForm, CustomerForm, InvoiceForm, InvoiceItemFormSet

class ProductCreateView(CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'invoices/product_form.html'  
    success_url = reverse_lazy('product_list')

class ProductListView(ListView):
    model = Product
    template_name = 'invoices/product_list.html' 
    context_object_name = 'products'

class CustomerListView(ListView):
    model = Customer
    template_name = 'invoices/customer_list.html'
    context_object_name = 'customers'

class CustomerCreateView(CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'invoices/customer_form.html'
    success_url = reverse_lazy('customer_list')

class InvoiceListView(ListView):
    model = Invoice
    template_name = 'invoices/invoice_list.html'
    context_object_name = 'invoices'
    ordering = ['-created_at'] 

def invoice_create_view(request):
    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        formset = InvoiceItemFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            invoice = form.save()
            
            formset.instance = invoice
            formset.save() 
            
            return redirect('invoice_list')
    else:
        form = InvoiceForm()
        formset = InvoiceItemFormSet()
        
    return render(request, 'invoices/invoice_form.html', {
        'form': form,
        'formset': formset
    })
def invoice_create_view(request):
    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        formset = InvoiceItemFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    invoice = form.save()
                    formset.instance = invoice
                    formset.save()
                    invoice.calculate_totals()
                
                return redirect('invoice_list')
            except Exception as e:
                print(f"Database write exception: {str(e)}")
    else:
        form = InvoiceForm()
        formset = InvoiceItemFormSet()
        
    return render(request, 'invoices/invoice_form.html', {
        'form': form,
        'formset': formset
    })

def invoice_list_view(request):
    invoices = Invoice.objects.all()
    return render(request, 'invoices/invoice_list.html', {'invoices': invoices})

LineItemFormSet = inlineformset_factory(
    Invoice,
    InvoiceItem, 
    fields=('product', 'quantity', 'tax_rate'), 
    extra=1,
    can_delete=True
)

def invoice_detail_view(request, pk):
   
    invoice = get_object_or_404(Invoice, pk=pk)
    
    if request.method == 'POST':
        invoice_form = InvoiceForm(request.POST, instance=invoice)
        formset = LineItemFormSet(request.POST, request.FILES, instance=invoice)
        
        if invoice_form.is_valid() and formset.is_valid():
            invoice_form.save()
            formset.save()
            return redirect('invoice_detail', pk=invoice.pk)
   
    else:
        invoice_form = InvoiceForm(instance=invoice)
        formset = LineItemFormSet(instance=invoice)
        
    context = {
        'invoice': invoice,
        'invoice_form': invoice_form,
        'formset': formset,
    }
    return render(request, 'invoices/invoice_detail.html', context)

def compile_pdf_with_playwright(html_content):
    """Helper function to generate PDF using headless Chromium"""
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
    line_items = invoice.line_items.all()

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
        return redirect('invoice_detail', pk=invoice.id)

    line_items = invoice.line_items.all()

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
            from_email='billing@charleenafrica.com',
            to=[invoice.customer.email]
        )
        
        email.attach(f"Invoice_{invoice.id:04d}.pdf", pdf_data, 'application/pdf')
        email.send()
        
        messages.success(request, f"Official PDF Invoice successfully compiled and dispatched to {invoice.customer.email}!")
        
    except Exception as e:
        messages.error(request, f"Encountered systemic fault routing email dispatch: {str(e)}")

    return redirect('invoice_detail', pk=invoice.id)