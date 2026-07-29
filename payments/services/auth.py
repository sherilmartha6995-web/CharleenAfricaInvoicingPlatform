import base64
import requests
from django.conf import settings

def get_mpesa_access_token():
    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET
    
    auth_str = f"{consumer_key}:{consumer_secret}"
    encoded_auth = base64.b64encode(auth_str.encode()).decode()
    
    api_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    headers = {"Authorization": f"Basic {encoded_auth}"}

    response = requests.get(api_url, headers=headers)

    
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise Exception(f"Failed to retrieve M-Pesa access token: {response.text}")