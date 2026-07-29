from django.urls import path
from . import views
from .views import ProductCreateView, ProductListView, CustomerListView, CustomerCreateView,InvoiceListView, invoice_create_view, invoice_detail_view, invoice_pdf_view

app_name = 'invoices'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('products/', ProductListView.as_view(), name='product_list'),
    path('products/add/', ProductCreateView.as_view(), name='product_add'),
    path('customers/', CustomerListView.as_view(), name='customer_list'),
    path('customers/add/', CustomerCreateView.as_view(), name='customer_add'),
    path('customers/<int:pk>/edit/', views.CustomerUpdateView.as_view(), name='customer_edit'),
    path('customers/<int:pk>/delete/', views.CustomerDeleteView.as_view(), name='customer_delete'),
    path('invoices/', InvoiceListView.as_view(), name='invoice_list'),
    path('invoices/add/', invoice_create_view, name='invoice_add'),
    path('invoices/<uuid:invoice_uuid>/', views.invoice_detail_view, name='invoice_detail'),
    path('invoice/<int:invoice_id>/send-email/', views.send_invoice_email_view, name='send_invoice_email'),
    path('invoice/<int:pk>/pdf/', views.invoice_pdf_view, name='invoice_pdf'),
    path('invoice/<int:invoice_id>/add-credit-note/', views.create_credit_note, name='create_credit_note'),
    path('invoice/<int:invoice_id>/add-debit-note/', views.create_debit_note, name='create_debit_note'),
    path('credit-notes/', views.credit_note_list_view, name='credit_note_list'),
    path('debit-notes/', views.debit_note_list_view, name='debit_note_list'),
    path('switch-business/<int:business_id>/', views.set_active_business, name='set_active_business'),
    path('businesses/', views.business_list_view, name='business_list'),
    path('register-business/', views.register_business_view, name='register_business'),
    path('invoice/<int:invoice_id>/add-pod/', views.create_pod, name='create_pod'),
    path('pay/<uuid:invoice_uuid>/', views.customer_invoice_view, name='customer_invoice_view'),
    path('pay/<uuid:invoice_uuid>/process/', views.process_customer_payment, name='process_customer_payment'),
]