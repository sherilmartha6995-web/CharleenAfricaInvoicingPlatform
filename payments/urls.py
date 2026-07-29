from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('pay/<int:invoice_id>/', views.pay_invoice, name='pay_invoice'),
    path('callback/', views.mpesa_callback, name='mpesa_callback'),
    path('list/', views.payment_list, name='payment_list'),
]