from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from database import get_db
from api.deps import get_current_active_user
from models.user import User
import schemas.inventory as schemas
import crud.inventory as crud

router = APIRouter()

@router.post("/tasks", response_model=schemas.InventoryTaskResponse)
def create_task(task_in: schemas.InventoryTaskCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return crud.create_inventory_task(db, task_in)

@router.get("/tasks", response_model=List[schemas.InventoryTaskResponse])
def list_tasks(skip: int = 0, limit: int = 20, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return crud.get_inventory_tasks(db, skip, limit)

@router.post("/tasks/{task_id}/submit", response_model=schemas.InventoryRecordResponse)
def submit_record(task_id: str, submit_in: schemas.InventorySubmit, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    record, result_msg = crud.submit_inventory_record(db, task_id, submit_in.asset_code, current_user.id)
    if not record:
        raise HTTPException(status_code=400, detail=result_msg)
    
    # 核心修复：注入资产的详细物理信息，返回给 App 显示
    record.asset_code = record.asset.asset_code
    record.asset_name = record.asset.dynamic_attributes.get("设备名称", "未命名资产")
    return record

@router.get("/tasks/{task_id}/records", response_model=List[schemas.InventoryRecordResponse])
def get_records(task_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    # 简单实现，获取该任务下所有记录
    from models.asset import InventoryRecord, Asset
    results = db.query(InventoryRecord).join(Asset).filter(InventoryRecord.task_id == task_id).all()
    # 补全响应模型所需字段
    for r in results:
        r.asset_code = r.asset.asset_code
        # 安全读取，防止动态属性为 None 时报错
        attrs = r.asset.dynamic_attributes or {}
        r.asset_name = attrs.get("设备名称", "未知设备")
    return results

@router.delete("/tasks/{task_id}")
def delete_task(task_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    from models.asset import InventoryTask, InventoryRecord
    task = db.query(InventoryTask).filter(InventoryTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 删除关联的记录
    db.query(InventoryRecord).filter(InventoryRecord.task_id == task_id).delete()
    # 删除任务主体
    db.delete(task)
    db.commit()
    return {"message": "任务已成功删除"}

@router.get("/tasks/{task_id}/export")
def export_records(task_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    from models.asset import InventoryRecord, Asset, InventoryTask
    import pandas as pd
    import io
    from fastapi.responses import StreamingResponse
    from urllib.parse import quote

    task = db.query(InventoryTask).filter(InventoryTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    results = db.query(InventoryRecord).join(Asset).filter(InventoryRecord.task_id == task_id).all()
    
    data = []
    for r in results:
        attrs = r.asset.dynamic_attributes or {}
        data.append({
            "资产编码": r.asset.asset_code,
            "资产名称": attrs.get("设备名称", "未知"),
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
