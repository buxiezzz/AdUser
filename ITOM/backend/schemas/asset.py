from pydantic import BaseModel, UUID4, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

# Employee Schemas
class EmployeeBase(BaseModel):
    name: str
    department: Optional[str] = None
    email: Optional[str] = None
    ad_account: Optional[str] = None

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeResponse(EmployeeBase):
    id: int
    created_at: datetime
    class Config:
        orm_mode = True

# Category Schemas
class CategoryBase(BaseModel):
    name: str
    default_attributes: Dict[str, Any] = {}

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    default_attributes: Optional[Dict[str, Any]] = None

class CategoryResponse(CategoryBase):
    id: int
    class Config:
        orm_mode = True

# Asset Schemas
class AssetBase(BaseModel):
    asset_code: Optional[str] = None
    category_id: int
    status: Optional[str] = "闲置"
    owner_id: Optional[int] = None
    dynamic_attributes: Dict[str, Any] = {}

class AssetCreate(AssetBase):
    pass

class AssetUpdate(BaseModel):
    asset_code: Optional[str] = None
    category_id: Optional[int] = None
    status: Optional[str] = None
    owner_id: Optional[int] = None
    dynamic_attributes: Optional[Dict[str, Any]] = None

class AssetResponse(AssetBase):
    id: UUID4
    qr_code_token: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    owner: Optional[EmployeeResponse] = None
    category: Optional[CategoryResponse] = None

    class Config:
        orm_mode = True

# Asset Log Schemas
class AssetLogCreate(BaseModel):
    asset_id: UUID4
    action: str
    previous_owner_id: Optional[int] = None
    new_owner_id: Optional[int] = None
    memo: Optional[str] = None

class AssetLogResponse(AssetLogCreate):
    id: int
    operated_by: int
    operator_name: Optional[str] = None
    previous_owner_name: Optional[str] = None
    new_owner_name: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True
