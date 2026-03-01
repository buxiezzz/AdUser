from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from crud import asset as crud_asset
import schemas.asset
from schemas.asset import AssetResponse, AssetCreate, CategoryResponse, CategoryCreate, EmployeeResponse, EmployeeCreate
from api.deps import get_current_active_user
from models.user import User
from models.asset import Employee
from core.ad_utils import search_ad_users
from api.routers.settings import load_config

router = APIRouter()

# --- Categories ---
@router.get("/categories", response_model=List[CategoryResponse])
def read_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return crud_asset.get_categories(db, skip=skip, limit=limit)

@router.post("/categories", response_model=CategoryResponse)
def create_category(category: CategoryCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return crud_asset.create_category(db, category=category)

@router.put("/categories/{category_id}", response_model=CategoryResponse)
def update_category(category_id: int, category_in: schemas.asset.CategoryUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    db_cat = crud_asset.update_category(db, category_id=category_id, category_in=category_in)
    if not db_cat:
        raise HTTPException(status_code=404, detail="Category not found")
    return db_cat

# --- Employees ---
@router.get("/employees", response_model=List[EmployeeResponse])
def read_employees(keyword: str = "", skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    # 优先从 AD 拉取名单包装成假 Employee 结构供前端下拉使用
    config = load_config()
    sys_bind_user = config.get('BIND_USERNAME', '')
    sys_bind_pass = config.get('BIND_PASSWORD', '')
    
    ad_users = search_ad_users(sys_bind_user, sys_bind_pass, keyword)
    results = []
    
    for au in ad_users:
        ad_account = au['username']
        # 查找本地库是否存在该用户
        db_emp = db.query(Employee).filter(Employee.ad_account == ad_account).first()
        
        name = au.get('display_name') or ad_account
        department = getattr(au, 'department', '') or au.get('dn', '').split(',')[1].replace('OU=', '')
        email = f"{ad_account}@{config.get('DOMAIN_NAME', 'stom.local')}"
        
        if not db_emp:
            db_emp = Employee(
                name=name,
                department=department,
                email=email,
                ad_account=ad_account
            )
            db.add(db_emp)
            db.commit()
            db.refresh(db_emp)
        else:
            # 如果信息有变动，也可以选择在这里更新 db_emp
            pass
            
        results.append(db_emp)
        
    return results

@router.post("/employees", response_model=EmployeeResponse)
def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return crud_asset.create_employee(db, employee=employee)

# --- Assets ---
@router.get("/", response_model=List[AssetResponse])
def read_assets(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return crud_asset.get_assets(db, skip=skip, limit=limit)

@router.post("/", response_model=AssetResponse)
def create_asset(asset: AssetCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return crud_asset.create_asset(db, asset=asset, current_user_id=current_user.id)

@router.get("/{asset_id}", response_model=AssetResponse)
def read_asset(asset_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    from uuid import UUID
    db_asset = crud_asset.get_asset(db, asset_id=UUID(asset_id))
    if db_asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    return db_asset

@router.put("/{asset_id}", response_model=AssetResponse)
def update_asset(asset_id: str, asset_in: schemas.asset.AssetUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    from uuid import UUID
    db_asset = crud_asset.update_asset(db, asset_id=UUID(asset_id), asset_in=asset_in, current_user_id=current_user.id)
    if not db_asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return db_asset

@router.delete("/{asset_id}", response_model=AssetResponse)
def delete_asset(asset_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    from uuid import UUID
    db_asset = crud_asset.delete_asset(db, asset_id=UUID(asset_id), current_user_id=current_user.id)
    if not db_asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return db_asset

@router.get("/{asset_id}/logs", response_model=List[schemas.asset.AssetLogResponse])
def read_asset_logs(asset_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    from uuid import UUID
    return crud_asset.get_asset_logs(db, asset_id=UUID(asset_id))
