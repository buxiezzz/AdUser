from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from api.deps import get_current_active_user, get_device_source
from models.user import User
from models.asset import Location # 增加导入
from schemas.asset import AssetTransferCreate, AssetTransferUpdate, AssetTransferResponse, AssetTransferBatchCreate
from crud.transfer import (
    get_transfers, create_transfer, update_transfer_status, get_transfer,
    create_batch_transfers
)
from crud.audit import log_action

router = APIRouter()

@router.get("/", response_model=List[AssetTransferResponse])
def list_transfers(
    skip: int = 0,
    limit: int = 100,
    location_id: Optional[int] = None,
    status: Optional[str] = None,
    keyword: Optional[str] = None,
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

    return get_transfers(
        db, skip=skip, limit=limit, 
        location_id=effective_location_id,
        status=status,
        keyword=keyword
    )

@router.post("/", response_model=AssetTransferResponse)
def create_new_transfer(
    transfer_in: AssetTransferCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    device: str = Depends(get_device_source)
):
    """
    发起跨归属地调拨申请。
    """
    try:
        result = create_transfer(db, transfer_in, applicant_id=current_user.id)
        # 获取地名用于口语化日志
        loc = db.query(Location).filter(Location.id == transfer_in.to_location_id).first()
        loc_name = loc.name if loc else f"ID:{transfer_in.to_location_id}"
        
        # 纠正参数：target 设为简短 ID，details 设为长描述
        log_action(db, (current_user.display_name or current_user.username), 'asset', 'TRANSFER_CREATE',
                   target=f"ASSET:{transfer_in.asset_id[:8]}", 
                   details=f"发起了调拨申请：目标地 [{loc_name}]",
                   device_source=device)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/batch/", response_model=List[AssetTransferResponse])
def create_batch_transfer_requests(
    batch_in: AssetTransferBatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    device: str = Depends(get_device_source)
):
    """
    批量发起跨归属地调拨申请。
    """
    try:
        results = create_batch_transfers(db, batch_in, applicant_id=current_user.id)
        # 获取地名用于口语化日志
        loc = db.query(Location).filter(Location.id == batch_in.to_location_id).first()
        loc_name = loc.name if loc else f"ID:{batch_in.to_location_id}"
        
        log_action(db, (current_user.display_name or current_user.username), 'asset', 'TRANSFER_BATCH_CREATE',
                   target=f"BATCH:{len(batch_in.asset_ids)}项",
                   details=f"一键批量发起了调拨申请：目标地 [{loc_name}]",
                   device_source=device)
        return results
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
    current_user: User = Depends(get_current_active_user),
    device: str = Depends(get_device_source)
):
    """
    更新调拨单状态（审批、发货、签收、拒绝）。
    """
    try:
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
        
        # 口语化描述
        status_text = update_in.status
        memo_prefix = {
            "待发货": "审批通过了调拨单",
            "运输中": "已执行资产从库房出库/发货",
            "已完成": "确认核收了调拨资产并完成入库",
            "已拒绝": "驳回了本次调拨申请"
        }.get(status_text, f"业务状态变更为: {status_text}")
        
        # 纠正参数顺序
        log_action(db, (current_user.display_name or current_user.username), 'asset', action,
                   target=f"BILL:{transfer_id[:8]}",
                   details=memo_prefix,
                   device_source=device)
        
        # 填充名称
        if result.applicant:
            result.applicant_name = result.applicant.username
        if result.approver:
            result.approver_name = result.approver.username
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
        # 填充名称
        if result.applicant:
            result.applicant_name = result.applicant.username
        if result.approver:
            result.approver_name = result.approver.username
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
