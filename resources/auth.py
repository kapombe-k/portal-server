from flask import request
from flask_restful import Resource
from flask_jwt_extended import create_access_token, create_refresh_token
from models import db, User
import bleach
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone

class SignUpResource(Resource):
    def post(self):
        data = request.get_json()

        if User.query.filter_by(phone=data.get("phone")).first():
            return {"message": "Phone number already in use"}, 400

        if User.query.filter_by(email=data.get("email")).first():
            return {"message": "Email already in use"}, 400

        required_fields = ["username", "phone", "email", "password"]
        for field in required_fields:
            if field not in data:
                return {"message": f"{field} is required"}, 400

        # Validate password
        is_valid, msg = User.validate_password(data["password"])
        if not is_valid:
            return {"message": msg}, 400

        try:
            new_user = User(
                username=bleach.clean(data["username"]),
                phone=bleach.clean(data["phone"]),
                email=bleach.clean(data["email"]),
                created_at=datetime.now(timezone.utc),
            )
            new_user.password = data["password"]  # This triggers the setter to hash
        except SQLAlchemyError as e:
            db.session.rollback()
            return {"message": "Error creating user", "error": str(e)}, 500

        db.session.flush()
        db.session.add(new_user)
        db.session.commit()
        return {"message": "User created successfully"}, 201
    
class LoginResource(Resource):
    def post(self):
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return {"message": "Email and password are required"}, 400

        user = User.query.filter_by(email=email).first()
        if not user or not user.verify_password(password):
            return {"message": "Invalid credentials"}, 401

        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "phone": user.phone
            }
        }, 200