from models import Transaction
from flask_jwt_extended import jwt_required
from flask_restful import Resource


class TransactionsResource(Resource):
    @jwt_required()
    def get(self):
        transactions = Transaction.query.all()

        return [{
            "id": transaction.id,
            "user_id": transaction.user_id,
            "amount": str(transaction.amount),
            "status": transaction.status,
            "created_at": transaction.created_at.isoformat()
        } for transaction in transactions], 200
    
    @jwt_required()
    def user_transactions(self, user_id):
        transactions = Transaction.query.filter_by(user_id=user_id).all()
        
        return [{
            "id": transaction.id,
            "user_id": transaction.user_id,
            "amount": str(transaction.amount),
            "status": transaction.status,
            "created_at": transaction.created_at.isoformat()
        } for transaction in transactions], 200
    
    @jwt_required()
    def transaction_details(self, transaction_id):
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            return {"message": "Transaction not found"}, 404
        
        return {
            "id": transaction.id,
            "user_id": transaction.user_id,
            "bundle_id": transaction.bundle_id,
            "mpesa_code": transaction.mpesa_code,
            "amount": str(transaction.amount),
            "status": transaction.status,
            "created_at": transaction.created_at.isoformat()
        }, 200
    
