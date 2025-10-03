from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required
from models import Session, Transaction, db
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

class SessionsResource(Resource):
    @jwt_required()
    def get(self):
        try:
            sessions = Session.query.all()
            sessions_list = [{
                'id': session.id,
                'user_id': session.user_id,
                'bundle_id': session.bundle_id,
                'session_token': session.session_token,
                'is_active': session.is_active,
                'transaction_id': session.transaction_id,
                'created_at': session.created_at.isoformat(),
                'expires_at': session.expires_at.isoformat()
            } for session in sessions]
            return {'sessions': sessions_list}, 200
        except SQLAlchemyError as e:
            return {'message': 'An error occurred while fetching sessions.', 'error': str(e)}, 500
        
    @jwt_required()
    def start_session(self):
        data = request.get_json()

        transaction_status = Transaction.query.get(data['transaction_id']).status
        if transaction_status != 'completed':
            return {'message': 'Transaction not completed. Cannot start session.'}, 400

        required_fields = ['user_id', 'bundle_id', 'session_token', 'transaction_id', 'expires_at']
        for field in required_fields:
            if field not in data:
                return {'message': f'{field} is required'}, 400

        try:
            new_session = Session(
                user_id=data['user_id'],
                bundle_id=data['bundle_id'],
                session_token=data['session_token'],
                transaction_id=data['transaction_id'],
                expires_at=data['expires_at']
            )
            db.session.add(new_session)
            db.session.commit()
            return {'message': 'Session started successfully', 'session_id': new_session.id}, 201
        except SQLAlchemyError as e:
            db.session.rollback()
            return {'message': 'An error occurred while starting the session.', 'error': str(e)}, 500
        
    @jwt_required()
    def end_session(self, session_id):
        try:
            session = Session.query.get(session_id)
            if not session:
                return {'message': 'Session not found'}, 404
            if not session.is_active:
                return {'message': 'Session is already inactive'}, 400
            if session.expires_at < datetime.now():
                session.is_active = False
                db.session.commit()
                return {'message': 'Session has expired'}, 400
            return {'message': 'Session ended successfully'}, 200
        except SQLAlchemyError as e:
            db.session.rollback()
            return {'message': 'An error occurred while ending the session.', 'error': str(e)}, 500