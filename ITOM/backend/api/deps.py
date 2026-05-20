from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from database import get_db
from core.security import SECRET_KEY, ALGORITHM
from crud.user import get_user_by_username
from schemas.user import TokenData
from models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="认证凭据失效",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="未激活的用户")
    return current_user

def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足")
    return current_user

def get_current_user_optional_query(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """支持从 Header 或 Query 参数中获取 Token，用于文件下载等 window.open 场景"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="认证凭据失效",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # 优先从 Authorization Header 读取
    final_token = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        final_token = auth_header.split(" ")[1]
    
    # 其次从 Query 参数读取（window.open 下载场景）
    if not final_token:
        final_token = request.query_params.get("token")
    
    if not final_token:
        raise credentials_exception
    
    # 直接解析 JWT，不通过依赖注入
    try:
        payload = jwt.decode(final_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception
    return user

def get_device_source(request: Request) -> str:
    """通过 User-Agent 自动识别请求来源终端"""
    from core.device import detect_device
    return detect_device(request)
