from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Any

from database import get_db
from crud import location as crud_location
from schemas.asset import LocationCreate, LocationUpdate, LocationResponse
from api.deps import get_current_active_user, get_current_admin_user, get_device_source
from crud.audit import log_action

router = APIRouter()


@router.get("/", response_model=List[LocationResponse])
def read_locations(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_active_user)
):
    """获取所有归属地列表"""
    return crud_location.get_locations(db, include_inactive=include_inactive)


@router.get("/{location_id}", response_model=LocationResponse)
def read_location(
    location_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_active_user)
):
    """获取单个归属地详情"""
    db_loc = crud_location.get_location(db, location_id)
    if not db_loc:
        raise HTTPException(status_code=404, detail="归属地不存在")
    return db_loc


@router.post("/", response_model=LocationResponse)
def create_location(
    location: LocationCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_active_user),
    device: str = Depends(get_device_source)
):
    """创建新归属地（仅集团超管）"""
    if not current_user.is_group_admin:
        raise HTTPException(status_code=403, detail="仅集团超管可管理归属地")

    # 检查编码是否重复
    existing = crud_location.get_location_by_code(db, location.code)
    if existing:
        raise HTTPException(status_code=400, detail=f"归属地编码 '{location.code}' 已存在")

    db_loc = crud_location.create_location(db, location)
    log_action(db, (current_user.display_name or current_user.username), 'system', 'CREATE_LOCATION', db_loc.name, device_source=device)
    return db_loc


@router.put("/{location_id}", response_model=LocationResponse)
def update_location(
    location_id: int,
    location_in: LocationUpdate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_active_user),
    device: str = Depends(get_device_source)
):
    """更新归属地信息（仅集团超管）"""
    if not current_user.is_group_admin:
        raise HTTPException(status_code=403, detail="仅集团超管可管理归属地")

    db_loc = crud_location.update_location(db, location_id, location_in)
    if not db_loc:
        raise HTTPException(status_code=404, detail="归属地不存在")

    log_action(db, (current_user.display_name or current_user.username), 'system', 'UPDATE_LOCATION', db_loc.name, device_source=device)
    return db_loc


@router.delete("/{location_id}")
def delete_location(
    location_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_active_user),
    device: str = Depends(get_device_source)
):
    """删除归属地（软删除，仅集团超管）"""
    if not current_user.is_group_admin:
        raise HTTPException(status_code=403, detail="仅集团超管可管理归属地")

    # 检查是否有资产关联
    from models.asset import Asset
    asset_count = db.query(Asset).filter(Asset.location_id == location_id).count()
    if asset_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"该归属地下仍有 {asset_count} 项资产，请先迁移或删除相关资产"
        )

    success = crud_location.delete_location(db, location_id)
    if not success:
        raise HTTPException(status_code=404, detail="归属地不存在")

    log_action(db, (current_user.display_name or current_user.username), 'system', 'DELETE_LOCATION', f"ID:{location_id}", device_source=device)
    return {"message": "归属地已停用"}
