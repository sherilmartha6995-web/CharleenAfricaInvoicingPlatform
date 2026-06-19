from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
import os

def email_invoice_to_customer(invoice, pdf_path):
    """
    Assembles and dispatches an email to the customer with the invoice PDF attached.
    """
    subject = f"Official Invoice #{invoice.id:04d} - Charleen Africa Invoicing"
    
    context = {
        'invoice': invoice,
        'customer_name': invoice.customer.name if invoice.customer else "Valued Client"
    }
    
    email_body = render_to_string('invoices/email_body.txt', context)
    
    email = EmailMessage(
        subject=subject,
        body=email_body,
        from_email=settings.EMAIL_HOST_USER,
        to=[invoice.customer.email],
    )
    
    if os.path.exists(pdf_path):
        with open(pdf_path, 'rb') as f:
            email.attach(f"invoice_{invoice.id:04d}.pdf", f.read(), 'application/pdf')
            
    email.send()