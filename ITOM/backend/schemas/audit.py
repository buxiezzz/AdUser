from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AuditLogBase(BaseModel):
    username: str
    module: str
    action: str
    target: str
    details: Optional[str] = None
    ip_address: Optional[str] = None
    device_source: Optional[str] = None

class AuditLog(AuditLogBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class AuditLogResponse(BaseModel):
    total: int
    items: list[AuditLog]
