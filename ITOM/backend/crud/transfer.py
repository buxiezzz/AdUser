from sqlalchemy.orm import Session, joinedload
from models.asset import Asset, AssetTransfer, AssetLog, Location
from models.user import User
from schemas.asset import AssetTransferCreate, AssetTransferUpdate, AssetTransferBatchCreate
import uuid

def get_transfer(db: Session, transfer_id: str):
    return db.query(AssetTransfer).filter(AssetTransfer.id == transfer_id).first()

def get_transfers(db: Session, skip: int = 0, limit: int = 100, 
                  location_id: int = None, status: str = None, keyword: str = None):
    query = db.query(AssetTransfer).join(Asset, isouter=True).options(
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
        
    if status:
        query = query.filter(AssetTransfer.status == status)
        
    if keyword:
        search = f"%{keyword}%"
        query = query.filter(
            (Asset.asset_code.ilike(search)) |
            (AssetTransfer.id.ilike(search)) # 支持按单号模糊搜
        )
    
    transfers = query.order_by(AssetTransfer.created_at.desc()).offset(skip).limit(limit).all()
    
    # ... (原有名称填充逻辑)
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
    
    if asset.status != "闲置":
        raise ValueError(f"资产当前状态为'{asset.status}'，仅‘闲置’状态的资产允许发起跨归属地调拨。")
    
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
    
    # 获取目标归属地名称用于日志记录
    target_loc = db.query(Location).filter(Location.id == transfer_in.to_location_id).first()
    loc_name = target_loc.name if target_loc else f"ID:{transfer_in.to_location_id}"

    # 记录资产日志
    log = AssetLog(
        asset_id=asset.id,
        operated_by=applicant_id,
        action="调拨申请",
        memo=f"发起了跨归属地调拨申请，目标归属地: {loc_name}"
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
        if not asset:
            raise ValueError("调拨关联的原始资产已不存在，无法完成签收")
        
        # 核心逻辑：更新资产归属地
        asset.location_id = db_transfer.to_location_id
        asset.status = "闲置" # 签收后默认闲置
        asset.owner_id = None # 跨区调拨完成后，强制清空原持有人
        
        # 清理原组织信息
        if asset.dynamic_attributes and "所属组织" in asset.dynamic_attributes:
            new_attrs = dict(asset.dynamic_attributes)
            new_attrs.pop("所属组织", None)
            asset.dynamic_attributes = new_attrs
        
        # 获取目标归属地名称用于日志记录
        target_loc = db.query(Location).filter(Location.id == db_transfer.to_location_id).first()
        loc_name = target_loc.name if target_loc else f"ID:{db_transfer.to_location_id}"

        # 记录资产变更日志
        log = AssetLog(
            asset_id=asset.id,
            operated_by=user_id,
            action="调拨签收",
            memo=f"跨归属地调拨完成，资产已到达新归属地({loc_name})并转为闲置状态"
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

def create_batch_transfers(db: Session, batch_in: AssetTransferBatchCreate, applicant_id: int):
    """
    批量创建调拨申请
    """
    results = []
    errors = []
    
    for asset_id in batch_in.asset_ids:
        try:
            # 构造单个调拨请求对象
            single_in = AssetTransferCreate(
                asset_id=asset_id,
                to_location_id=batch_in.to_location_id,
                memo=batch_in.memo
            )
            # 调用已有的创建逻辑（包含状态校验和日志记录）
            res = create_transfer(db, single_in, applicant_id)
            results.append(res)
        except ValueError as e:
            errors.append(f"资产 {asset_id}: {str(e)}")
            
    if errors and not results:
        # 如果全部失败，抛出汇总错误
        raise ValueError(" | ".join(errors))
        
    return results
