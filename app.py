import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from dotenv import load_dotenv
from models import db
from datetime import timedelta
from flask_jwt_extended import JWTManager

load_dotenv()

#FLASK APP INITIALIZATION
app = Flask(__name__)

#EXTENSIONS
db.init_app(app)
CORS(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
api = Api(app)

# database configuration
ENVIRONMENT = os.environ.get("ENVIRONMENT")
if ENVIRONMENT == "production":
    DATABASE_URL = os.environ.get("SUPABASE_URL")
else:
    DATABASE_URL = "DATABASE_URL"

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True

# JWT configuration
if ENVIRONMENT == "production":
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=15)
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)
else:
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=1)
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)
app.config["JWT_ALGORITHM"] = "HS256"
app.config["JWT_SECRET_KEY"] = os.environ.get("SECRET_KEY")

if __name__ == "__main__":
    app.run(debug=True)