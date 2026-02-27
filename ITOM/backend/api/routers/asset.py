from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from crud import asset as crud_asset
from schemas.asset import AssetResponse, AssetCreate, CategoryResponse, CategoryCreate, EmployeeResponse, EmployeeCreate
from api.deps import get_current_active_user
from models.user import User

router = APIRouter()

# --- Categories ---
@router.get("/categories", response_model=List[CategoryResponse])
def read_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return crud_asset.get_categories(db, skip=skip, limit=limit)

@router.post("/categories", response_model=CategoryResponse)
def create_category(category: CategoryCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return crud_asset.create_category(db, category=category)

# --- Employees ---
@router.get("/employees", response_model=List[EmployeeResponse])
def read_employees(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return crud_asset.get_employees(db, skip=skip, limit=limit)

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
