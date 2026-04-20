from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import SessionLocal
from crud import audit as audit_crud
from schemas import audit as audit_schema
from api.deps import get_current_active_user
from models.user import User

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=audit_schema.AuditLogResponse)
def read_audit_logs(
    module: str = Query(None, description="模块名，如 asset, ad"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    分页查询审计日志
    """
    total = audit_crud.count_logs(db, module=module)
    items = audit_crud.get_logs(db, module=module, skip=skip, limit=limit)
    return {"total": total, "items": items}
