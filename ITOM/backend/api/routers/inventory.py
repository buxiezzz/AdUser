from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from database import get_db
from api.deps import get_current_active_user, get_device_source, get_current_user_optional_query
from models.user import User
import schemas.inventory as schemas
import crud.inventory as crud
from crud.audit import log_action

router = APIRouter()

@router.post("/tasks", response_model=schemas.InventoryTaskResponse)
def create_task(task_in: schemas.InventoryTaskCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user), device: str = Depends(get_device_source)):
    if not current_user.is_group_admin:
        # 如果不是集团超管，强行将盘点任务的归属地设为当前用户所属归属地
        task_in.location_id = current_user.location_id
    res = crud.create_inventory_task(db, task_in)
    log_action(db, (current_user.display_name or current_user.username), 'inventory', 'INVENTORY_TASK_CREATE', task_in.name, device_source=device)
    return res

@router.get("/tasks", response_model=List[schemas.InventoryTaskResponse])
def list_tasks(skip: int = 0, limit: int = 20, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    loc_id = None if current_user.is_group_admin else current_user.location_id
    return crud.get_inventory_tasks(db, skip, limit, location_id=loc_id)

@router.post("/tasks/{task_id}/submit", response_model=schemas.InventoryRecordResponse)
def submit_record(task_id: str, submit_in: schemas.InventorySubmit, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    # 归属地边界越权校验
    from models.asset import InventoryTask
    task = db.query(InventoryTask).filter(InventoryTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if not current_user.is_group_admin and task.location_id != current_user.location_id:
        raise HTTPException(status_code=403, detail="您无权操作其他归属地的盘点任务")

    record, result_msg = crud.submit_inventory_record(db, task_id, submit_in.asset_code, current_user.id)
    if not record:
        raise HTTPException(status_code=400, detail=result_msg)
    
    # 核心修复：注入资产的详细物理信息，返回给 App 显示
    record.asset_code = record.asset.asset_code
    record.asset_name = record.asset.dynamic_attributes.get("设备名称", "未命名资产")
    return record

@router.get("/tasks/{task_id}/records", response_model=List[schemas.InventoryRecordResponse])
def get_records(task_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    # 归属地边界越权校验
    from models.asset import InventoryTask, InventoryRecord, Asset
    task = db.query(InventoryTask).filter(InventoryTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if not current_user.is_group_admin and task.location_id != current_user.location_id:
        raise HTTPException(status_code=403, detail="您无权查看其他归属地的盘点任务")

    # 简单实现，获取该任务下所有记录
    from sqlalchemy.orm import joinedload
    
    # 联表查询 Asset 和 Category
    results = db.query(InventoryRecord)\
        .join(Asset)\
        .options(joinedload(InventoryRecord.asset).joinedload(Asset.category))\
        .filter(InventoryRecord.task_id == task_id).all()
        
    # 补全响应模型所需字段
    for r in results:
        r.asset_code = r.asset.asset_code
        # 优先使用分类名称作为资产名称，更符合业务习惯
        r.asset_name = r.asset.category.name if r.asset.category else "未知设备"
    return results

@router.delete("/tasks/{task_id}")
def delete_task(task_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user), device: str = Depends(get_device_source)):
    from models.asset import InventoryTask, InventoryRecord
    task = db.query(InventoryTask).filter(InventoryTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if not current_user.is_group_admin and task.location_id != current_user.location_id:
        raise HTTPException(status_code=403, detail="您无权删除其他归属地的盘点任务")
    
    # 删除关联的记录
    db.query(InventoryRecord).filter(InventoryRecord.task_id == task_id).delete()
    # 删除任务主体
    task_name = task.name
    db.delete(task)
    db.commit()
    log_action(db, (current_user.display_name or current_user.username), 'inventory', 'INVENTORY_TASK_DELETE', task_name, device_source=device)
    return {"message": "任务已成功删除"}

@router.get("/tasks/{task_id}/export")
def export_records(task_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_optional_query)):
    from models.asset import InventoryRecord, Asset, InventoryTask
    from sqlalchemy.orm import joinedload
    import pandas as pd
    import io
    from fastapi.responses import StreamingResponse
    from urllib.parse import quote

    task = db.query(InventoryTask).filter(InventoryTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if current_user and not current_user.is_group_admin and task.location_id != current_user.location_id:
        raise HTTPException(status_code=403, detail="您无权导出其他归属地的盘点报告")

    results = db.query(InventoryRecord)\
        .join(Asset)\
        .options(joinedload(InventoryRecord.asset).joinedload(Asset.category))\
        .filter(InventoryRecord.task_id == task_id).all()
    
    data = []
    for r in results:
        data.append({
            "资产编码": r.asset.asset_code,
            "资产名称": r.asset.category.name if r.asset.category else "未知",
            "盘点状态": r.status,
            "核对人UID": r.operator_id or "未记录",
            "核对时间": r.audit_time.strftime("%Y-%m-%d %H:%M:%S") if r.audit_time else "—"
        })
    
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='盘点报告')
    
    output.seek(0)
    filename = quote(f"盘点报告_{task.name}.xlsx")
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"}
    )
