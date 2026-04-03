from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import io
import openpyxl
from uuid import UUID
from datetime import datetime, date

from database import get_db
from crud import asset as crud_asset
import schemas.asset
from schemas.asset import AssetResponse, AssetCreate, CategoryResponse, CategoryCreate, EmployeeResponse, EmployeeCreate
from api.deps import get_current_active_user
from models.user import User
from models.asset import Employee, Category, Asset, AssetLog
from core.ad_utils import search_ad_users
from api.routers.settings import load_config

router = APIRouter()

@router.get("/mobile/{qr_code_token}", response_model=AssetResponse)
def read_asset_by_qr(qr_code_token: str, db: Session = Depends(get_db)):
    """
    移动端专用：免密通过扫码Token获取资产详细档案
    """
    asset = crud_asset.get_asset_by_qr_token(db, qr_code_token)
    if not asset:
        raise HTTPException(status_code=404, detail="无法找到该资产或二维码已失效")
    return asset

class StatusUpdateRequest(schemas.asset.BaseModel):
    status: str

@router.post("/{asset_id}/inventory", response_model=dict)
def quick_inventory_check(asset_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """
    移动端专用：免密扫码快速生成一条“盘点核对”日志
    """
    log_entry = crud_asset.record_inventory_check(db, asset_id, current_user.id)
    return {"message": "盘点记录已入账", "log_id": log_entry.id}

@router.patch("/{asset_id}/status", response_model=AssetResponse)
def quick_update_status(asset_id: UUID, request: StatusUpdateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """
    移动端专用：快速变更设备周转状态
    """
    db_asset = crud_asset.update_asset_status(db, asset_id, request.status, current_user.id)
    if not db_asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return db_asset

class ReassignRequest(schemas.asset.BaseModel):
    owner_id: int

@router.patch("/{asset_id}/reassign", response_model=AssetResponse)
def reassign_asset_owner(asset_id: UUID, request: ReassignRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """
    移动端专用：快速调拨/更改资产归属人
    """
    db_asset = crud_asset.reassign_asset(db, asset_id, request.owner_id, current_user.id)
    if not db_asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return db_asset

# --- Categories ---
@router.get("/categories", response_model=List[CategoryResponse])
def read_categories(skip: int = 0, limit: int = 10000, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return crud_asset.get_categories(db, skip=skip, limit=limit)

@router.post("/categories", response_model=CategoryResponse)
def create_category(category: CategoryCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return crud_asset.create_category(db, category=category)

@router.put("/categories/{category_id}", response_model=CategoryResponse)
def update_category(category_id: int, category_in: schemas.asset.CategoryUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    db_cat = crud_asset.update_category(db, category_id=category_id, category_in=category_in)
    if not db_cat:
        raise HTTPException(status_code=404, detail="Category not found")
    return db_cat

@router.delete("/categories/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    # Check if any assets belong to this category before deleting
    assets = db.query(Asset).filter(Asset.category_id == category_id).first()
    if assets:
        raise HTTPException(status_code=400, detail="Cannot delete category because there are assets linked to it. Delete or move the assets first.")
        
    success = crud_asset.delete_category(db, category_id=category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deleted successfully"}

# --- Employees ---
@router.get("/employees", response_model=List[EmployeeResponse])
def read_employees(keyword: str = "", skip: int = 0, limit: int = 10000, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    # 优先从 AD 拉取名单包装成假 Employee 结构供前端下拉使用
    config = load_config()
    sys_bind_user = config.get('BIND_USERNAME', '')
    sys_bind_pass = config.get('BIND_PASSWORD', '')
    
    ad_users = search_ad_users(sys_bind_user, sys_bind_pass, keyword)
    results = []
    
    for au in ad_users:
        ad_account = au['username']
        # 查找本地库是否存在该用户
        db_emp = db.query(Employee).filter(Employee.ad_account == ad_account).first()
        
        name = au.get('display_name') or ad_account
        department = getattr(au, 'department', '') or au.get('dn', '').split(',')[1].replace('OU=', '')
        email = f"{ad_account}@{config.get('DOMAIN_NAME', 'stom.local')}"
        
        if not db_emp:
            db_emp = Employee(
                name=name,
                department=department,
                email=email,
                ad_account=ad_account
            )
            db.add(db_emp)
            db.commit()
            db.refresh(db_emp)
        else:
            # 如果信息有变动，也可以选择在这里更新 db_emp
            pass
            
        results.append(db_emp)
        
    return results

@router.post("/employees", response_model=EmployeeResponse)
def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return crud_asset.create_employee(db, employee=employee)

# --- Excel Import ---
@router.post("/import")
async def import_assets(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload an Excel file.")

    contents = await file.read()
    try:
        workbook = openpyxl.load_workbook(io.BytesIO(contents), data_only=True)
        sheet = workbook.active
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read Excel file: {str(e)}")

    rows = list(sheet.iter_rows(values_only=True))
    if not rows or len(rows) < 2:
        raise HTTPException(status_code=400, detail="Excel file is empty or missing headers.")

    headers = rows[0]
    
    # 建立实际列名到索引的映射
    header_idx = {str(h).strip(): i for i, h in enumerate(headers) if h}

    # 支持的表头别名映射表
    alias_mapping = {
        "资产编号": ["资产编号", "资产编码"],
        "当前状态": ["当前状态", "资产状态"],
        "设备分类": ["设备分类", "资产分类", "资产名称"],
        "使用者": ["使用者AD账号", "使用人", "使用者", "员工名", "责任人"]
    }
    
    # 查找核心列的索引
    core_idx = {}
    for core_key, aliases in alias_mapping.items():
        for alias in aliases:
            if alias in header_idx:
                core_idx[core_key] = header_idx[alias]
                break

    if "资产编号" not in core_idx:
        raise HTTPException(status_code=400, detail="缺少必填表头: 资产编号 / 资产编码")

    success_count = 0
    errors = []

    # Prepare AD configuration for employee matching (if needed)
    config = load_config()
    sys_bind_user = config.get('BIND_USERNAME', '')
    sys_bind_pass = config.get('BIND_PASSWORD', '')

    def parse_excel_val(val):
        if val is None:
            return ""
        if isinstance(val, float) and val.is_integer():
            return str(int(val))
        return str(val).strip()

    for row_num, row in enumerate(rows[1:], start=2):
        try:
            asset_code_original = row[core_idx["资产编号"]]
            if not asset_code_original:
                continue
            
            asset_code = parse_excel_val(asset_code_original)
            status_val = row[core_idx["当前状态"]] if "当前状态" in core_idx else None
            status = parse_excel_val(status_val) if status_val else "闲置"
            
            cat_val = row[core_idx["设备分类"]] if "设备分类" in core_idx else None
            category_name = parse_excel_val(cat_val) if cat_val else "未知分类"
            
            owner_val = row[core_idx["使用者"]] if "使用者" in core_idx else None
            owner_name = parse_excel_val(owner_val)

            # 1. Process Category
            category = db.query(Category).filter(Category.name == category_name).first()
            if not category:
                category = Category(name=category_name, default_attributes={})
                db.add(category)
                db.flush() # flush to get the ID

            # 2. Process Employee
            owner_id = None
            if owner_name and status not in ["闲置", "报废"]:
                employee = db.query(Employee).filter(Employee.ad_account == owner_name).first()
                if not employee:
                    employee = db.query(Employee).filter(Employee.name == owner_name).first()
                
                if not employee:
                    # 从 AD 查询员工
                    try:
                        ad_users = search_ad_users(sys_bind_user, sys_bind_pass, owner_name)
                        if ad_users:
                            au = ad_users[0]
                            ad_account = au['username']
                            # 关键修复：先按 ad_account 检查 DB，避免重复 INSERT
                            employee = db.query(Employee).filter(Employee.ad_account == ad_account).first()
                            if not employee:
                                name = au.get('display_name') or owner_name
                                department = getattr(au, 'department', '') or au.get('dn', '').split(',')[1].replace('OU=', '')
                                email = f"{ad_account}@{config.get('DOMAIN_NAME', 'stom.local')}"
                                employee = Employee(name=name, department=department, email=email, ad_account=ad_account)
                                db.add(employee)
                                db.flush()
                    except Exception as e:
                        print(f"Failed to lookup AD for {owner_name}: {e}")
                
                if not employee:
                    # AD 中没找到，建立本地账户（按名字查重避免重复）
                    dept_col_idx = header_idx.get("所属组织") or header_idx.get("使用部门") or header_idx.get("部门")
                    dept_name = parse_excel_val(row[dept_col_idx]) if dept_col_idx is not None and row[dept_col_idx] else "迁移产生部门"
                    local_ad = f"local_{owner_name}"
                    employee = db.query(Employee).filter(Employee.ad_account == local_ad).first()
                    if not employee:
                        employee = Employee(
                            name=owner_name,
                            department=dept_name,
                            email=f"local_{owner_name}@migration.local",
                            ad_account=local_ad
                        )
                        db.add(employee)
                        db.flush()
                
                if employee:
                    owner_id = employee.id

            # 3. Dynamic Attributes Processing
            # 除了四个核心系统字段（从映射表中反向查出对应的中文字面量）之外，全丢入 dynamic_attributes
            used_headers = []
            for k in core_idx.values():
                for header_key, idx in header_idx.items():
                    if idx == k:
                        used_headers.append(header_key)
                        
            dynamic_attributes = {}
            for col_name, col_idx in header_idx.items():
                if col_name not in used_headers:
                    k = parse_excel_val(headers[col_idx])
                    v = parse_excel_val(row[col_idx])
                    dynamic_attributes[k] = v

            # 4. Check if asset exists, if not create, if yes update
            asset = db.query(Asset).filter(Asset.asset_code == asset_code).first()
            is_new = False
            if not asset:
                asset = Asset(
                    asset_code=asset_code,
                    category_id=category.id,
                    status=status,
                    owner_id=owner_id,
                    dynamic_attributes=dynamic_attributes
                )
                db.add(asset)
                is_new = True
            else:
                asset.category_id = category.id
                asset.status = status
                asset.owner_id = owner_id
                asset.dynamic_attributes = dynamic_attributes

            db.flush()

            # 4.5 如果 Excel 表格内有“入库日期”列，解析后覆盖 created_at
            date_col_idx = core_idx.get("入库日期") or header_idx.get("入库日期") or header_idx.get("入库日期") or header_idx.get("购入日期")
            if date_col_idx is not None:
                date_val = row[date_col_idx]
                parsed_date = None
                if isinstance(date_val, (datetime, date)):
                    parsed_date = datetime(date_val.year, date_val.month, date_val.day, 0, 0, 0) if isinstance(date_val, date) else date_val
                elif date_val:
                    try:
                        s = str(date_val).strip()
                        for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日", "%m/%d/%Y"]:
                            try:
                                parsed_date = datetime.strptime(s[:10], fmt)
                                break
                            except ValueError:
                                continue
                    except Exception:
                        pass
                if parsed_date:
                    asset.created_at = parsed_date
                    db.flush()
            
            # 5. Log Action
            action_desc = "系统批量导入-新增" if is_new else "系统批量导入-更新"
            # It's better to flush earlier and get asset.id, but since Asset id is UUID default func uuid4, it's populated locally or flush populates it.
            log = AssetLog(
                asset_id=asset.id,
                operated_by=current_user.id,
                action=action_desc,
                new_owner_id=owner_id,
                memo=f"通过Excel一键导入, 行号: {row_num}"
            )
            db.add(log)
            success_count += 1
            db.commit()  # 每行成功后立即提交，防止后续行回滚影响已成功的行

        except Exception as row_error:
            db.rollback()  # 回滚本行，清除 Session 污染状态，不影响下一行
            errors.append(f"Row {row_num}: {str(row_error)}")
            continue

    return {
        "message": f"Import completed. Success: {success_count}, Errors: {len(errors)}",
        "success": success_count,
        "errors": errors
    }

# --- Batch Operations ---
from pydantic import BaseModel as PydanticBase
from typing import Optional as Opt

class BatchDeleteBody(PydanticBase):
    asset_ids: List[str]

class BatchUpdateBody(PydanticBase):
    asset_ids: List[str]
    status: Opt[str] = None
    owner_id: Opt[int] = None

class BatchCopyBody(PydanticBase):
    asset_ids: List[str]

@router.post("/batch-delete")
def batch_delete_assets(body: BatchDeleteBody, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """彻底删除（硬删除）选中的多个资产"""
    results = []
    for id_str in body.asset_ids:
        try:
            success = crud_asset.hard_delete_asset(db, asset_id=id_str)
            if success:
                results.append(id_str)
        except Exception as e:
            pass
    return {"deleted": len(results), "ids": results}

@router.put("/batch-update")
def batch_update_assets(body: BatchUpdateBody, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """批量修改状态 / 使用人"""
    import schemas.asset as sa
    updated = 0
    for id_str in body.asset_ids:
        try:
            update_data: dict = {}
            if body.status is not None:
                update_data["status"] = body.status
            if body.owner_id is not None:
                update_data["owner_id"] = body.owner_id
            if not update_data:
                continue
            asset_in = sa.AssetUpdate(**update_data)
            result = crud_asset.update_asset(db, asset_id=_UUID(id_str), asset_in=asset_in, current_user_id=current_user.id)
            if result:
                updated += 1
        except Exception:
            pass
    return {"updated": updated}

@router.post("/batch-copy")
def batch_copy_assets(body: BatchCopyBody, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """复制选中资产，生成新的资产编码（原编码 + -COPY-N）"""
    import uuid as _uuid
    created = 0
    for id_str in body.asset_ids:
        try:
            from uuid import UUID as _UUID
            src = crud_asset.get_asset(db, asset_id=_UUID(id_str))
            if not src:
                continue
            # 生成不重复的新编码
            suffix = 1
            while True:
                new_code = f"{src.asset_code}-COPY-{suffix}"
                exists = db.query(Asset).filter(Asset.asset_code == new_code).first()
                if not exists:
                    break
                suffix += 1
            new_asset = Asset(
                asset_code=new_code,
                category_id=src.category_id,
                status="闲置",
                owner_id=None,
                dynamic_attributes=dict(src.dynamic_attributes or {}),
                qr_code_token=_uuid.uuid4().hex
            )
            db.add(new_asset)
            db.flush()
            log = AssetLog(asset_id=new_asset.id, operated_by=current_user.id, action="批量复制", memo=f"复制自 {src.asset_code}")
            db.add(log)
            db.commit()
            created += 1
        except Exception as e:
            db.rollback()
    return {"created": created}

# --- Assets ---
@router.get("/", response_model=List[AssetResponse])
def read_assets(keyword: str = "", status: str = "", skip: int = 0, limit: int = 10000, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return crud_asset.get_assets(db, skip=skip, limit=limit, keyword=keyword, status=status)

@router.post("/", response_model=AssetResponse)
def create_asset(asset: AssetCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return crud_asset.create_asset(db, asset=asset, current_user_id=current_user.id)

@router.get("/{asset_id}", response_model=AssetResponse)
def read_asset(asset_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    db_asset = crud_asset.get_asset(db, asset_id=asset_id)
    if db_asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    return db_asset

@router.put("/{asset_id}", response_model=AssetResponse)
def update_asset(asset_id: str, asset_in: schemas.asset.AssetUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    db_asset = crud_asset.update_asset(db, asset_id=asset_id, asset_in=asset_in, current_user_id=current_user.id)
    if not db_asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return db_asset

@router.delete("/{asset_id}", response_model=AssetResponse)
def delete_asset(asset_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    db_asset = crud_asset.delete_asset(db, asset_id=asset_id, current_user_id=current_user.id)
    if not db_asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return db_asset

@router.delete("/hard/{asset_id}")
def hard_delete_asset(asset_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    success = crud_asset.hard_delete_asset(db, asset_id=asset_id)
    if not success:
        raise HTTPException(status_code=404, detail="Asset not found")
    return {"message": "Asset completely deleted"}

@router.get("/{asset_id}/logs", response_model=List[schemas.asset.AssetLogResponse])
def get_asset_logs(asset_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return crud_asset.get_asset_logs(db, asset_id=asset_id)
