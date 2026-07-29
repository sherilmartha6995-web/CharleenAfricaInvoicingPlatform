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
        amount_to_pay = float(request.POST.get('amount'))

        if amount_to_pay > float(invoice.remaining_balance):
            return JsonResponse({"error": "Amount exceeds remaining balance."}, status=400)
        
        response = initiate_stk_push(phone_number, amount_to_pay, invoice.invoice_number)
        return JsonResponse(response)
    return render(request, 'payments/pay.html', {'invoice': invoice})

@csrf_exempt
def mpesa_callback(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        stk_callback = data.get('Body', {}).get('stkCallback', {})
        checkout_id = stk_callback.get('CheckoutRequestID')
        result_code = stk_callback.get('ResultCode')

        try:
            mpesa_txn = MpesaTransaction.objects.get(checkout_request_id=checkout_id)
            payment = mpesa_txn.payment
            
            if result_code == 0:
                payment.status = 'COMPLETED'
            else:
                payment.status = 'FAILED'
            payment.save() 
            
            mpesa_txn.raw_callback = stk_callback
            mpesa_txn.save()
            
        except MpesaTransaction.DoesNotExist:
            return JsonResponse({"error": "Transaction not found"}, status=404)

        return JsonResponse({"ResultCode": 0, "ResultDesc": "Success"})
    return JsonResponse({"error": "Invalid request"}, status=400)

def payment_list(request):
    payments = Payment.objects.all().order_by('-created_at')
    return render(request, 'payments/payment_list.html', {'payments': payments})