from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required
from models import db
from models.bundles import Bundles
from sqlalchemy.exc import SQLAlchemyError
import bleach
from datetime import datetime

class BundlesResource(Resource):
    def get(self):
        bundles = Bundles.query.all()

        return [{
            "id": bundle.id,
            "name": bundle.name,
            "description": bundle.description,
            "price": bundle.price,
            "created_at": bundle.created_at.isoformat()
        } for bundle in bundles], 200
    
    @jwt_required()
    def post(self):
        data = request.get_json()

        required_fields = ['name', 'description', 'price']
        for field in required_fields:
            if field not in data:
                return {'message': f'{field} is required'}, 400
        
        try:
            new_bundle = Bundles (
                name = bleach.clean(data['name']),
                description = bleach.clean(data['description']),
                price = data['price'],
                created_at = datetime.timezone.eat.now()
            )
        except SQLAlchemyError as e:
            db.session.rollback()
            return {'message': 'Error creating bundle', 'error': str(e)}, 500

        db.session.flush()
        db.session.add(new_bundle)
        db.session.commit()
        return {"message": "Bundle created successfully"}, 201
    
    @jwt_required()
    def patch(self, bundle_id):
        data = request.get_json()
        bundle = Bundles.query.get(bundle_id)
        if not bundle:
            return {"message": "Bundle not found"}, 404

        if 'name' in data:
            bundle.name = bleach.clean(data['name'])
        if 'description' in data:
            bundle.description = bleach.clean(data['description'])
        if 'price' in data:
            bundle.price = data['price']
        
        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            return {'message': 'Error updating bundle', 'error': str(e)}, 500

        return {"message": "Bundle updated successfully"}, 200
    
    @jwt_required()
    def delete(self, bundle_id):
        bundle = Bundles.query.get(bundle_id)
        if not bundle:
            return {"message": "Bundle not found"}, 404
        
        try:
            db.session.delete(bundle)
            db.session.commit()
            db
        except SQLAlchemyError as e:
            db.session.rollback()
            return {'message': 'Error deleting bundle', 'error': str(e)}, 500

        return {"message": "Bundle deleted successfully"}, 200
       
