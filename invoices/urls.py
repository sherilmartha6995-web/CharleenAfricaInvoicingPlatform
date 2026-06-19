from django.urls import path
from . import views
from .views import ProductCreateView, ProductListView, CustomerListView, CustomerCreateView,InvoiceListView, invoice_create_view, invoice_detail_view, invoice_pdf_view

urlpatterns = [
    path('', ProductListView.as_view(), name='product_list'),
    path('products/add/', ProductCreateView.as_view(), name='product_add'),
    path('customers/', CustomerListView.as_view(), name='customer_list'),
    path('customers/add/', CustomerCreateView.as_view(), name='customer_add'),
    path('invoices/', InvoiceListView.as_view(), name='invoice_list'),
    path('invoices/add/', invoice_create_view, name='invoice_add'),
    path('invoices/<int:pk>/', invoice_detail_view, name='invoice_detail'),
    path('invoices/<int:pk>/pdf/', invoice_pdf_view, name='invoice_pdf'),
    path('invoice/<int:invoice_id>/send-email/', views.send_invoice_email_view, name='send_invoice_email'),
    path('invoice/<int:pk>/pdf/', views.invoice_pdf_view, name='invoice_pdf'),
]