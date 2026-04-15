from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from pydantic import BaseModel
from database import get_db
from core.security import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, verify_password, get_password_hash
from crud.user import get_user_by_username, create_user
from models.user import User
from schemas.user import Token, UserResponse, UserCreate
from api.deps import get_current_active_user
from api.routers.settings import load_config

router = APIRouter()

@router.post("/login", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user_by_username(db, username=form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="该账号未被分配权限",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # 第一层：检查本地数据库密码
    is_valid = verify_password(form_data.password, user.hashed_password)
    
    # 第二层：如果本地密码不对，尝试 AD 域验证 (双重回源模式)
    if not is_valid:
        from ldap3 import Server, Connection, Tls
        import ssl
        config = load_config()
        dc_ip = config.get('DOMAIN_CONTROLLER_IP', '')
        domain_name = config.get('DOMAIN_NAME', '')
        
        if dc_ip and domain_name:
            try:
                tls_config = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLS_CLIENT)
                server = Server(dc_ip, port=636, use_ssl=True, tls=tls_config)
                # 尝试通过 AD 验证凭据
                upn = f"{form_data.username}@{domain_name}"
                conn = Connection(server, user=upn, password=form_data.password, auto_bind=True)
                if conn.bound:
                    is_valid = True
                conn.unbind()
            except Exception as e:
                print(f"AD Auth Fallback Error: {e}")

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="密码错误 或 AD域验证失败",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=UserResponse)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    config_data = load_config()
    if not config_data.get("ALLOW_REGISTRATION", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="系统已关闭自助注册，请联系管理员分配账号"
        )
        
    user = get_user_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=400,
            detail="用户名已存在",
        )
    return create_user(db, user_in)

class PasswordChange(BaseModel):
    old_password: str
    new_password: str

@router.post("/change-password")
def change_password(data: PasswordChange, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """修改当前登录用户的密码"""
    if not verify_password(data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="原密码输入错误"
        )
    
    current_user.hashed_password = get_password_hash(data.new_password)
    db.commit()
    return {"message": "密码已成功修改"}

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user = Depends(get_current_active_user), db: Session = Depends(get_db)):
    # 手动附加归属地名称用于前端展示
    if current_user.location_id and current_user.location:
        current_user.location_name = current_user.location.name
    else:
        current_user.location_name = "集团总部" if current_user.is_group_admin else "未分配"
    return current_user
