from flask_restful import Resource
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db
from models import User
from sqlalchemy.exc import SQLAlchemyError
import bleach
class UserResource(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return {"message": "User not found"}, 404
        return {
            "id": user.id,
            "username": user.username,
            "phone": user.phone,
            "email": user.email,
            "sessions": [session.id for session in user.sessions],
            "transactions": [transaction.id for transaction in user.transactions],
            "created_at": user.created_at.isoformat()
        }, 200
       
    @jwt_required()
    def patch(self):
        
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return {"message": "User not found"}, 404
        
        data = request.get_json()
        required_fields = ['username', 'phone', 'email', 'password']
        for field in required_fields:
            if field in data:
                setattr(user, field, data[field])
                try:
                    if field == 'email':
                        user.email = bleach.clean(data['email'])
                    elif field == 'username':
                        user.username = bleach.clean(data['username'])
                    elif field == 'phone':
                        user.phone = bleach.clean(data['phone'])
                    elif field == 'password':
                        user.password = data['password']
                except SQLAlchemyError as e:
                    db.session.rollback()
                    return {'message': 'Error updating user', 'error': str(e)}, 500
                
                db.session.add(user)
                db.session.commit()
                return {"message": "User updated successfully"}, 200

    @jwt_required()
    def delete(self):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return {"message": "User not found"}, 404
        
        try:
            db.session.delete(user)
            db.session.commit()
            return {"message": "User deleted successfully"}, 200
        except SQLAlchemyError as e:
            db.session.rollback()
            return {'message': 'Error deleting user', 'error': str(e)}, 500

