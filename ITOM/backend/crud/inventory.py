from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from models.asset import Asset, InventoryTask, InventoryRecord
from schemas.inventory import InventoryTaskCreate, InventorySubmit

def create_inventory_task(db: Session, task_in: InventoryTaskCreate):
    # 1. 创建任务主体
    db_task = InventoryTask(
        name=task_in.name,
        description=task_in.description,
        start_time=task_in.start_time,
        status="进行中"
    )
    db.add(db_task)
    db.flush()

    # 2. 筛选资产范围 (如果有特定列表则按列表，否则默认为全部在册资产)
    query = db.query(Asset).filter(Asset.status.notin_(["报废", "下账"]))
    if task_in.asset_ids:
        query = query.filter(Asset.id.in_([str(aid) for aid in task_in.asset_ids]))
    
    target_assets = query.all()
    db_task.total_count = len(target_assets)

    # 3. 批量生成盘点明细
    for asset in target_assets:
        record = InventoryRecord(
            task_id=db_task.id,
            asset_id=asset.id,
            status="未盘点"
        )
        db.add(record)
    
    db.commit()
    db.refresh(db_task)
    return db_task

def get_inventory_tasks(db: Session, skip: int = 0, limit: int = 20):
    return db.query(InventoryTask).order_by(InventoryTask.created_at.desc()).offset(skip).limit(limit).all()

def submit_inventory_record(db: Session, task_id: str, asset_code: str, operator_id: int):
    # 1. 查找资产并定位该任务下的记录
    asset = db.query(Asset).filter(Asset.asset_code == asset_code).first()
    if not asset:
        return None, "资产编码不存在"
    
    if asset.status in ["报废", "下账"]:
        return None, f"该资产处于【{asset.status}】状态，禁止盘点"
    
    record = db.query(InventoryRecord).filter(
        InventoryRecord.task_id == task_id,
        InventoryRecord.asset_id == asset.id
    ).first()
    
    if not record:
        return None, "该资产不在此次盘点范围内"
    
    if record.status == "已盘点":
        return record, "资产已核对，请勿重复操作"

    # 2. 更新记录
    record.status = "已盘点"
    record.audit_time = datetime.utcnow()
    record.operator_id = operator_id
    
    # 3. 同步更新任务进度
    task = db.query(InventoryTask).filter(InventoryTask.id == task_id).first()
    if task:
        task.finished_count += 1
        if task.finished_count >= task.total_count:
            task.status = "已完成"
            task.end_time = datetime.utcnow()
            
    db.commit()
    db.refresh(record)
    return record, "核对成功"
