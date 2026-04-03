import os
import sys

# 将当前目录添加到路径以便导入项目模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from database import SessionLocal
from models.user import User
from core.security import get_password_hash

def reset_password(username: str, new_password: str):
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            print(f"Error: User '{username}' not found.")
            return False
        
        user.hashed_password = get_password_hash(new_password)
        db.commit()
        print(f"Success: Password for user '{username}' has been reset to '{new_password}'.")
        return True
    except Exception as e:
        print(f"Error resetting password: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    # 默认将 admin 的密码重置为 admin123
    reset_password("admin", "admin123")
