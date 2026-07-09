def handle_mpesa_callback(data):
    print("Received M-Pesa Callback:", data)
    return {"status": "success"}