from flask_restful import Resource
from flask import request
import requests
import base64
import os
from datetime import datetime, timezone, timedelta
from models import db, Transaction, Bundle
from flask_jwt_extended import jwt_required, get_jwt_identity

class MpesaResource(Resource):
    def get_access_token(self):
        consumer_key = os.environ.get('MPESA_CONSUMER_KEY')
        consumer_secret = os.environ.get('MPESA_CONSUMER_SECRET')
        api_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
        response = requests.get(api_url, auth=(consumer_key, consumer_secret))
        if response.status_code == 200:
            return response.json()['access_token']
        else:
            return None

    def normalize_phone(self, phone: str) -> str:
        """Ensure phone number is in 2547XXXXXXXX format"""
        if phone.startswith("0"):
            return "254" + phone[1:]
        elif phone.startswith("+"):
            return phone[1:]
        return phone

    @jwt_required()
    def post(self):
        # Initiate STK Push
        data = request.get_json()

        # Validate data
        required = ['phone', 'amount', 'plan', 'mac_address', 'ip_address']
        for field in required:
            if field not in data:
                return {'message': f'{field} is required'}, 400

        phone = self.normalize_phone(data['phone'])
        amount = data['amount']
        plan = data['plan']
        mac_address = data['mac_address']
        ip_address = data['ip_address']
        transaction_desc = data.get('transaction_desc', "Payment for service")

        # Find bundle
        bundle = Bundle.query.filter_by(name=plan).first()
        if not bundle:
            return {'message': 'Bundle not found'}, 404

        user_id = get_jwt_identity()

        # Create transaction
        transaction = Transaction(
            user_id=user_id,
            bundle_id=bundle.id,
            amount=amount,
            status='pending',
            mac_address=mac_address,
            ip_address=ip_address
        )
        db.session.add(transaction)
        db.session.flush()
        account_reference = plan

        # Get access token
        access_token = self.get_access_token()
        if not access_token:
            return {'message': 'Failed to get access token'}, 500

        # Prepare STK Push data
        shortcode = os.environ.get('MPESA_SHORTCODE')
        passkey = os.environ.get('MPESA_PASSKEY')
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
        password = base64.b64encode((shortcode + passkey + timestamp).encode()).decode()

        stk_data = {
            "BusinessShortCode": shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone,
            "PartyB": shortcode,
            "PhoneNumber": phone,
            "CallBackURL": f"{os.environ.get('BASE_URL')}/mpesa/callback",
            "AccountReference": account_reference,
            "TransactionDesc": transaction_desc
        }

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        stk_url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'

        try:
            response = requests.post(stk_url, json=stk_data, headers=headers, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            return {'message': 'STK Push request failed', 'error': str(e)}, 500

        resp_data = response.json()
        # Update transaction with checkout_request_id
        transaction.checkout_request_id = resp_data.get('CheckoutRequestID')
        db.session.commit()
        return resp_data, 200

class MpesaCallbackResource(Resource):
    def post(self):
        # Handle callback
        data = request.get_json()

        # Parse the callback data
        body = data.get('Body', {})
        stk_callback = body.get('stkCallback', {})
        checkout_request_id = stk_callback.get('CheckoutRequestID')
        result_code = stk_callback.get('ResultCode')

        # Find transaction by checkout_request_id
        transaction = Transaction.query.filter_by(checkout_request_id=checkout_request_id).first()
        if not transaction:
            return {'message': 'Transaction not found'}, 404

        if result_code == 0:
            # Success
            callback_metadata = stk_callback.get('CallbackMetadata', {}).get('Item', [])
            mpesa_receipt_number = None
            transaction_date = None
            for item in callback_metadata:
                if item['Name'] == 'MpesaReceiptNumber':
                    mpesa_receipt_number = item['Value']
                elif item['Name'] == 'TransactionDate':
                    transaction_date = item['Value']

            transaction.mpesa_code = mpesa_receipt_number
            transaction.status = 'completed'
            transaction.transaction_date = transaction_date

            # Calculate expiry time based on bundle
            bundle = Bundle.query.get(transaction.bundle_id)
            # Assuming bundle.duration is in hours
            duration_hours = int(bundle.duration.split()[0]) if bundle.duration else 24
            transaction.expires_at = datetime.utcnow() + timedelta(hours=duration_hours)

            # AUTHORIZE ON ROUTER
            from resources.router import RouterManager
            router = RouterManager()
            comment = f"user:{transaction.user_id}|bundle:{bundle.name}|tx:{transaction.id}"
            success = router.authorize_mac(transaction.mac_address, transaction.ip_address, comment)
            router.disconnect()

            if not success:
                transaction.status = 'failed_authorization'

        else:
            # Failed
            transaction.status = 'failed'

        db.session.commit()
        return {'message': 'Callback processed'}, 200

