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
    location_id: Optional[int] = None
    created_at: datetime
    class Config:
        from_attributes = True

# Location Schemas
class LocationBase(BaseModel):
    code: str
    name: str
    address: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None

class LocationCreate(LocationBase):
    pass

class LocationUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    address: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    is_active: Optional[bool] = None

class LocationResponse(LocationBase):
    id: int
    is_active: bool = True
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

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
        from_attributes = True

# Asset Schemas
class AssetBase(BaseModel):
    asset_code: Optional[str] = None
    category_id: int
    status: Optional[str] = "闲置"
    owner_id: Optional[int] = None
    location_id: Optional[int] = None
    dynamic_attributes: Dict[str, Any] = {}

class AssetCreate(AssetBase):
    pass

class AssetUpdate(BaseModel):
    asset_code: Optional[str] = None
    category_id: Optional[int] = None
    status: Optional[str] = None
    owner_id: Optional[int] = None
    location_id: Optional[int] = None
    dynamic_attributes: Optional[Dict[str, Any]] = None

class AssetResponse(AssetBase):
    id: UUID4
    qr_code_token: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    owner: Optional[EmployeeResponse] = None
    category: Optional[CategoryResponse] = None
    location: Optional[LocationResponse] = None

    class Config:
        from_attributes = True

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
        from_attributes = True

# Asset Transfer Schemas
class AssetTransferBase(BaseModel):
    asset_id: str
    to_location_id: int
    memo: Optional[str] = None

class AssetTransferCreate(AssetTransferBase):
    pass

class AssetTransferUpdate(BaseModel):
    status: Optional[str] = None # 待发货, 运输中, 已完成, 已拒绝
    approver_id: Optional[int] = None
    tracking_number: Optional[str] = None
    memo: Optional[str] = None

class AssetTransferResponse(AssetTransferBase):
    id: str
    from_location_id: int
    status: str
    applicant_id: int
    approver_id: Optional[int] = None
    tracking_number: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    asset: Optional[AssetResponse] = None
    from_location: Optional[LocationResponse] = None
    to_location: Optional[LocationResponse] = None
    # 注意：这里可能需要 UserResponse，如果 main.py 已经有了可以引用，或者简化显示名称
    applicant_name: Optional[str] = None
    approver_name: Optional[str] = None

    class Config:
        from_attributes = True
