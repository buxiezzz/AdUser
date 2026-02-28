from database import SessionLocal
from models.user import User
from core.security import get_password_hash

db = SessionLocal()
admin = db.query(User).filter(User.username == "admin").first()
if admin:
    print("Found admin user. Resetting password to 'admin123'...")
    admin.hashed_password = get_password_hash("admin123")
    db.commit()
    print("Password reset successful!")
else:
    print("Admin user not found.")
db.close()
