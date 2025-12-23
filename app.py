import os
from flask import Flask
from flask_restful import Api
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from dotenv import load_dotenv
from models import db
from datetime import timedelta
from flask_jwt_extended import JWTManager
from resources.users import UserResource
from resources.bundles import BundleResource
from resources.sessions import SessionsResource
from resources.transaction import TransactionsResource
from resources.mpesa import MpesaResource, MpesaCallbackResource
from resources.auth import SignUpResource, LoginResource
from scheduler import start_scheduler

load_dotenv()

#FLASK APP INITIALIZATION
app = Flask(__name__)

# database configuration
ENVIRONMENT = os.environ.get("ENVIRONMENT")
if ENVIRONMENT == "production":
    DATABASE_URL = os.environ.get("SUPABASE_URL")
else:
    DATABASE_URL = os.environ.get("DATABASE_URL")

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True

#EXTENSIONS
db.init_app(app)
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")
CORS(app, origins=[FRONTEND_URL, "http://localhost:5173"])
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
api = Api(app)

# JWT configuration
if ENVIRONMENT == "production":
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=15)
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)
else:
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=1)
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)
app.config["JWT_ALGORITHM"] = "HS256"
app.config["JWT_SECRET_KEY"] = os.environ.get("SECRET_KEY")

# Add resources to API
api.add_resource(
    UserResource, "/users", "/users/<int:user_id>", "/users/<int:user_id>/transactions", "/users/<int:user_id>/sessions"
)
api.add_resource(BundleResource, '/bundles', '/bundles/<int:bundle_id>')
api.add_resource(SessionsResource, '/sessions', '/sessions/<int:session_id>', '/sessions/<int:user_id>/user_sessions')
api.add_resource(
    TransactionsResource,
    "/transactions",
    "/transactions/<int:transaction_id>",
    "/<int:user_id>/transactions",
)
api.add_resource(MpesaResource, '/mpesa/stkpush')
api.add_resource(MpesaCallbackResource, '/mpesa/callback')
api.add_resource(SignUpResource, '/auth/signup')
api.add_resource(LoginResource, '/auth/login')

if __name__ == "__main__":
    start_scheduler()
    app.run(debug=True)