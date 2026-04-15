from sqlalchemy.orm import Session, joinedload
from models.asset import Asset, AssetTransfer, AssetLog, Location
from models.user import User
from schemas.asset import AssetTransferCreate, AssetTransferUpdate
import uuid

def get_transfer(db: Session, transfer_id: str):
    return db.query(AssetTransfer).filter(AssetTransfer.id == transfer_id).first()

def get_transfers(db: Session, skip: int = 0, limit: int = 100, location_id: int = None):
    query = db.query(AssetTransfer).options(
        joinedload(AssetTransfer.asset),
        joinedload(AssetTransfer.from_location),
        joinedload(AssetTransfer.to_location),
        joinedload(AssetTransfer.applicant),
        joinedload(AssetTransfer.approver)
    )
    
    if location_id:
        # 调出地或调入地相关的单子
        query = query.filter(
            (AssetTransfer.from_location_id == location_id) | 
            (AssetTransfer.to_location_id == location_id)
        )
    
    transfers = query.order_by(AssetTransfer.created_at.desc()).offset(skip).limit(limit).all()
    
    # 填充名称（如果关系没有自动填充或需要扁平化处理）
    for t in transfers:
        if t.applicant:
            t.applicant_name = t.applicant.username
        if t.approver:
            t.approver_name = t.approver.username
            
    return transfers

def create_transfer(db: Session, transfer_in: AssetTransferCreate, applicant_id: int):
    # 获取资产当前归属地
    asset = db.query(Asset).filter(Asset.id == transfer_in.asset_id).first()
    if not asset:
        raise ValueError("资产不存在")
    
    # 检查是否已经在调拨中
    existing = db.query(AssetTransfer).filter(
        AssetTransfer.asset_id == transfer_in.asset_id,
        AssetTransfer.status.in_(["待审批", "待发货", "运输中"])
    ).first()
    if existing:
        raise ValueError("该资产已在调拨流程中，请勿重复申请")

    db_transfer = AssetTransfer(
        asset_id=transfer_in.asset_id,
        from_location_id=asset.location_id,
        to_location_id=transfer_in.to_location_id,
        memo=transfer_in.memo,
        applicant_id=applicant_id,
        status="待审批"
    )
    db.add(db_transfer)
    
    # 记录资产日志
    log = AssetLog(
        asset_id=asset.id,
        operated_by=applicant_id,
        action="调拨申请",
        memo=f"发起了跨归属地调拨申请，目标归属地ID: {transfer_in.to_location_id}"
    )
    db.add(log)
    
    db.commit()
    db.refresh(db_transfer)
    return db_transfer

def update_transfer_status(db: Session, transfer_id: str, update_in: AssetTransferUpdate, user_id: int):
    db_transfer = get_transfer(db, transfer_id)
    if not db_transfer:
        return None
    
    asset = db.query(Asset).filter(Asset.id == db_transfer.asset_id).first()
    old_status = db_transfer.status
    new_status = update_in.status or old_status
    
    if new_status == old_status and not update_in.tracking_number:
        return db_transfer

    # 逻辑处理
    if new_status == "待发货" and old_status == "待审批":
        db_transfer.approver_id = user_id
    elif new_status == "运输中" and old_status == "待发货":
        if update_in.tracking_number:
            db_transfer.tracking_number = update_in.tracking_number
        # 资产状态标记为调拨中
        asset.status = "调拨中"
    elif new_status == "已完成" and old_status == "运输中":
        # 核心逻辑：更新资产归属地
        asset.location_id = db_transfer.to_location_id
        asset.status = "闲置" # 签收后默认闲置
        
        # 记录资产变更日志
        log = AssetLog(
            asset_id=asset.id,
            operated_by=user_id,
            action="调拨签收",
            memo=f"跨归属地调拨完成，新归属地: {db_transfer.to_location_id}"
        )
        db.add(log)
    elif new_status == "已拒绝" and old_status == "待审批":
        db_transfer.approver_id = user_id
        db_transfer.memo = update_in.memo or db_transfer.memo
    
    db_transfer.status = new_status
    if update_in.memo:
        db_transfer.memo = update_in.memo
        
    db.commit()
    db.refresh(db_transfer)
    return db_transfer
