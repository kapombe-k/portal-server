from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData, Numeric
from sqlalchemy.orm import validates, relationship
from sqlalchemy_serializer import SerializerMixin
from datetime import datetime
from flask_bcrypt import generate_password_hash, check_password_hash
import re

convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)
db = SQLAlchemy(metadata=metadata)

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(), nullable=False)

    # relationships
    transactions = db.relationship("Transaction", backref="user", lazy=True)
    sessions = db.relationship("Session", backref="user", lazy=True)

    def __repr__(self):
        return f"<User {self.phone}>"
    
    @validates('email')
    def validate_email(self, key, address):
        if address:
            if not re.match(r"[^@]+@[^@]+\.[^@]+", address):
                raise ValueError("Invalid email address")
        return address
    
    @validates('phone')
    def validate_phone(self, key, phone):
        if len(phone) != 10 or not phone.isdigit():
            return ValueError("Phone number must be 10 digits")
        return phone
    
    @property
    def password(self):
        raise AttributeError("password is write-only")

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password).decode('utf8')

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def validate_password(password):
        if len(password) < 8:
            return False, "Password must be at least 8 characters"
        return True, ""
    
class Bundle(db.Model, SerializerMixin):
    __tablename__ = "bundles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    data_amount = db.Column(db.String(50), nullable=False)  # e.g., "1 GB", "5 GB"
    duration = db.Column(db.String(50), nullable=False)
    price = db.Column(Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(), nullable=False)

    # relationships
    transactions = db.relationship("Transaction", backref="bundle", lazy=True)

    def __repr__(self):
        return f"<Bundle {self.name}>"
    
class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    bundle_id = db.Column(db.Integer, db.ForeignKey('bundles.id'), nullable=False)
    mpesa_code = db.Column(db.String(100), unique=True, nullable=True)
    amount = db.Column(Numeric(10, 2), nullable=False)
    status = db.Column(db.String(50), nullable=False)  # e.g., 'pending', 'completed', 'failed'
    checkout_request_id = db.Column(db.String(100), nullable=True)
    transaction_date = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now(), nullable=False)
    mac_address = db.Column(db.String(17), nullable=False)
    ip_address = db.Column(db.String(15), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=True)  # To track when access should end
    session = db.relationship("Session", backref="transaction", uselist=False)

    def __repr__(self):
        return f"<Transaction {self.id} - User {self.user_id} - Bundle {self.bundle_id}>"
    
    def check_mpesa_code(self, code):
        return self.mpesa_code == code
    
    def update_status(self, new_status):
        self.status = new_status
        db.session.commit()
    
class Session(db.Model):
    __tablename__ = "sessions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    bundle_id = db.Column(db.Integer, db.ForeignKey('bundles.id'), nullable=False)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), nullable=True)
    session_token = db.Column(db.String(255), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f"<Session {self.session_token} for User {self.user_id}>"
    
class Admin(db.Model):
    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(50), default="SUPPORT")  # SUPERADMIN, MANAGER, SUPPORT
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(), nullable=False)

    # relationships
    audit_logs = db.relationship("AuditLog", backref="admin", lazy=True)

    def __repr__(self):
        return f"<Admin {self.email} - {self.role}>"


class SupportTicket(db.Model):
    __tablename__ = "support_tickets"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default="OPEN")  # OPEN, IN_PROGRESS, RESOLVED, CLOSED
    created_at = db.Column(db.DateTime, default=datetime.now(), nullable=False)

    # relationship
    user = db.relationship("User", backref="tickets")

    def __repr__(self):
        return f"<Ticket {self.id} - {self.status}>"


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("admins.id"), nullable=False)
    action = db.Column(db.String(255), nullable=False)   # e.g. "CREATE_BUNDLE"
    entity = db.Column(db.String(100), nullable=False)   # e.g. "Bundle"
    entity_id = db.Column(db.Integer, nullable=True)     # Which record was affected
    timestamp = db.Column(db.DateTime, default=datetime.now(), nullable=False)

    def __repr__(self):
        return f"<AuditLog {self.action} - {self.entity} ({self.entity_id})>"

