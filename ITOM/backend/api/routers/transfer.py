from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from api.deps import get_current_active_user
from models.user import User
from schemas.asset import AssetTransferCreate, AssetTransferUpdate, AssetTransferResponse
from crud.transfer import get_transfers, create_transfer, update_transfer_status, get_transfer
from crud.audit import log_action

router = APIRouter()

@router.get("/", response_model=List[AssetTransferResponse])
def list_transfers(
    skip: int = 0,
    limit: int = 100,
    location_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取调拨单列表。
    非集团超管只能看到与自身归属地相关的调拨单。
    """
    effective_location_id = location_id
    if not current_user.is_group_admin and current_user.location_id:
        effective_location_id = current_user.location_id

    return get_transfers(db, skip=skip, limit=limit, location_id=effective_location_id)

@router.post("/", response_model=AssetTransferResponse)
def create_new_transfer(
    transfer_in: AssetTransferCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    发起跨归属地调拨申请。
    """
    try:
        result = create_transfer(db, transfer_in, applicant_id=current_user.id)
        log_action(db, current_user.username, 'asset', 'TRANSFER_CREATE',
                   f"资产 {transfer_in.asset_id} -> 归属地 {transfer_in.to_location_id}")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{transfer_id}", response_model=AssetTransferResponse)
def read_transfer(
    transfer_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取单个调拨单详情"""
    t = get_transfer(db, transfer_id)
    if not t:
        raise HTTPException(status_code=404, detail="调拨单不存在")
    # 填充名称
    if t.applicant:
        t.applicant_name = t.applicant.username
    if t.approver:
        t.approver_name = t.approver.username
    return t

@router.put("/{transfer_id}", response_model=AssetTransferResponse)
def update_transfer(
    transfer_id: str,
    update_in: AssetTransferUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    更新调拨单状态（审批、发货、签收、拒绝）。
    """
    result = update_transfer_status(db, transfer_id, update_in, user_id=current_user.id)
    if not result:
        raise HTTPException(status_code=404, detail="调拨单不存在")
    
    action_map = {
        "待发货": "TRANSFER_APPROVE",
        "运输中": "TRANSFER_SHIP",
        "已完成": "TRANSFER_RECEIVE",
        "已拒绝": "TRANSFER_REJECT"
    }
    action = action_map.get(update_in.status, "TRANSFER_UPDATE")
    log_action(db, current_user.username, 'asset', action,
               f"调拨单 {transfer_id} -> {update_in.status}")
    
    # 填充名称
    if result.applicant:
        result.applicant_name = result.applicant.username
    if result.approver:
        result.approver_name = result.approver.username
    return result
