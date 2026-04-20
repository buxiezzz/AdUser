from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Any
from pydantic import BaseModel
from typing import Optional

from database import get_db
from crud import user as crud_user
from schemas.user import UserCreate, UserResponse
from api.deps import get_current_active_user
from crud.audit import log_action

router = APIRouter()

class UserUpdateParams(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    location_id: Optional[int] = None
    password: Optional[str] = None

@router.get("/", response_model=List[UserResponse])
def get_users_list(
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_active_user)
):
    """获取系统下所有账号列表（仅集团超管可视全部，且仅集团超管可管理）"""
    if not current_user.is_group_admin:
        raise HTTPException(status_code=403, detail="仅集团超管拥有权限分配账号")
        
    users = crud_user.get_users(db, limit=1000)
    for u in users:
        # 手动映射名称供前端友善展示
        if u.location_id and u.location:
             u.location_name = u.location.name
        else:
             u.location_name = "集团总部" if u.is_group_admin else "未分配"
    return users

@router.post("/", response_model=UserResponse)
def create_new_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_active_user)
):
    """创建新用户（分配归属地账号）"""
    if not current_user.is_group_admin:
        raise HTTPException(status_code=403, detail="仅集团超管可分配账号")
        
    existing = crud_user.get_user_by_username(db, user_in.username)
    if existing:
        raise HTTPException(status_code=400, detail="登录名已存在")
        
    db_user = crud_user.create_user(db, user_in)
    log_action(db, current_user.username, 'system', 'CREATE_ACCOUNT', db_user.username)
    
    if db_user.location_id and db_user.location:
        db_user.location_name = db_user.location.name
    return db_user

@router.put("/{user_id}", response_model=UserResponse)
def update_existing_user(
    user_id: int,
    user_in: UserUpdateParams,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_active_user)
):
    """修改用户信息及所属地"""
    if not current_user.is_group_admin:
        raise HTTPException(status_code=403, detail="仅集团超管可管理账号")
        
    db_user = crud_user.get_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="账号不存在")
        
    update_data = user_in.dict(exclude_unset=True)
    db_user = crud_user.update_user(db, user_id, update_data)
    
    log_action(db, current_user.username, 'system', 'UPDATE_ACCOUNT', db_user.username)
    
    if db_user.location_id and db_user.location:
        db_user.location_name = db_user.location.name
    else:
        db_user.location_name = "集团总部" if db_user.is_group_admin else "未分配"
        
    return db_user

@router.delete("/{user_id}")
def delete_existing_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_active_user)
):
    """删除账号"""
    if not current_user.is_group_admin:
        raise HTTPException(status_code=403, detail="仅集团超管可管理账号")
        
    db_user = crud_user.get_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="账号不存在")
        
    if db_user.username == "admin":
        raise HTTPException(status_code=400, detail="系统默认超管不可删除")
        
    crud_user.delete_user(db, user_id)
    log_action(db, current_user.username, 'system', 'DELETE_ACCOUNT', db_user.username)
    
    return {"message": "账号已删除"}
