from pydantic import BaseModel, UUID4, Field
from typing import Optional, List
from datetime import datetime

# 盘点记录（单笔资产）
class InventoryRecordBase(BaseModel):
    asset_id: UUID4
    status: str = "未盘点"  # 未盘点, 已盘点, 盘亏

class InventoryRecordResponse(InventoryRecordBase):
    id: int
    asset_code: Optional[str] = None
    asset_name: Optional[str] = None
    audit_time: Optional[datetime] = None
    operator_name: Optional[str] = None
    
    class Config:
        from_attributes = True

# 盘点任务
class InventoryTaskBase(BaseModel):
    name: str
    description: Optional[str] = None
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None

class InventoryTaskCreate(InventoryTaskBase):
    # 创建任务时可以选择的范围逻辑（简单起见，目前支持全量或按列表）
    asset_ids: Optional[List[UUID4]] = None

class InventoryTaskResponse(InventoryTaskBase):
    id: UUID4
    status: str  # 进行中, 已完成, 已取消
    total_count: int
    finished_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# 盘点提交执行（移动端使用）
class InventorySubmit(BaseModel):
    asset_code: str
