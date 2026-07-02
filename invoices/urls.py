from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from . import views
from .views import ProductCreateView, ProductListView, CustomerListView, CustomerCreateView,InvoiceListView, invoice_create_view, invoice_detail_view, invoice_pdf_view

urlpatterns = [
    path('', ProductListView.as_view(), name='product_list'),
    path('products/add/', ProductCreateView.as_view(), name='product_add'),
    path('customers/', CustomerListView.as_view(), name='customer_list'),
    path('customers/add/', CustomerCreateView.as_view(), name='customer_add'),
    path('customers/<int:pk>/edit/', views.CustomerUpdateView.as_view(), name='customer_edit'),
    path('customers/<int:pk>/delete/', views.CustomerDeleteView.as_view(), name='customer_delete'),
    path('invoices/', InvoiceListView.as_view(), name='invoice_list'),
    path('invoices/add/', invoice_create_view, name='invoice_add'),
    path('invoices/<uuid:invoice_uuid>/', views.invoice_detail_view, name='invoice_detail'),
    path('invoices/<int:pk>/pdf/', invoice_pdf_view, name='invoice_pdf'),
    path('invoice/<int:invoice_id>/send-email/', views.send_invoice_email_view, name='send_invoice_email'),
    path('invoice/<int:pk>/pdf/', views.invoice_pdf_view, name='invoice_pdf'),
    path('register/', views.register_view, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='invoices/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('invoice/<int:invoice_id>/add-credit-note/', views.create_credit_note, name='create_credit_note'),
    path('invoice/<int:invoice_id>/add-debit-note/', views.create_debit_note, name='create_debit_note'),
    path('credit-notes/', views.credit_note_list_view, name='credit_note_list'),
    path('debit-notes/', views.debit_note_list_view, name='debit_note_list'),
    path('switch-business/<int:business_id>/', views.set_active_business, name='set_active_business'),
    path('businesses/', views.business_list_view, name='business_list'),
    path('register-business/', views.register_business_view, name='register_business'),
]