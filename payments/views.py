import json
from .models import Payment, MpesaTransaction
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .services import initiate_stk_push
from invoices.models import Invoice
from .utils import format_phone_number

def pay_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    if request.method == "POST":
        phone_number = format_phone_number(request.POST.get('phone'))
        amount = invoice.total_amount
        
        response = initiate_stk_push(phone_number, amount, invoice.invoice_number)
        return JsonResponse(response)
    return render(request, 'payments/pay.html', {'invoice': invoice})

@csrf_exempt
def mpesa_callback(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        
        print("M-Pesa Callback Data:", data)
        
        return JsonResponse({"ResultCode": 0, "ResultDesc": "Success"})
    
    return JsonResponse({"error": "Invalid request"}, status=400)

