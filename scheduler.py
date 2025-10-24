from apscheduler.schedulers.background import BackgroundScheduler
from models import Transaction, db
from resources.router import RouterManager
from datetime import datetime
from app import app  # Import your Flask app instance

def cleanup_expired_sessions():
    """Finds expired sessions and removes their MAC authorization from the router."""
    with app.app_context():
        print("Running session cleanup job...")
        expired_transactions = Transaction.query.filter(
            Transaction.expires_at < datetime.utcnow(),
            Transaction.status == 'completed'
        ).all()

        if not expired_transactions:
            return

        router = RouterManager()
        for tx in expired_transactions:
            print(f"Expiring session for MAC: {tx.mac_address}")
            router.remove_authorization(tx.mac_address)
            tx.status = 'expired'

        router.disconnect()
        db.session.commit()
        print(f"Cleaned up {len(expired_transactions)} expired sessions.")

def start_scheduler():
    scheduler = BackgroundScheduler()
    # Run job every 5 minutes
    scheduler.add_job(cleanup_expired_sessions, 'interval', minutes=5)
    scheduler.start()
    print("Scheduler started.")