from sqlalchemy.orm import Session, joinedload
from uuid import UUID
import uuid

from models.asset import Asset, Category, Employee, AssetLog
from models.user import User
from schemas.asset import AssetCreate, AssetUpdate, CategoryCreate, CategoryUpdate, EmployeeCreate

# ====== Employee CRUD ======
def get_asset_by_qr_token(db: Session, token: str):
    return db.query(Asset).options(
        joinedload(Asset.category),
        joinedload(Asset.owner)
    ).filter(
        (Asset.qr_code_token == token) | (Asset.asset_code == token)
    ).first()

def record_inventory_check(db: Session, asset_id: str, user_id: int):
    # 创建一条盘点日志
    db_asset = get_asset(db, asset_id)
    if not db_asset:
        raise ValueError("资产不存在")
        
    if db_asset.status in ["报废", "下账"]:
        raise ValueError(f"资产当前为【{db_asset.status}】状态，禁止盘点")
    log_entry = AssetLog(
        asset_id=db_asset.id,
        operated_by=user_id,
        action="Inventory Check",
        memo="移动端通过扫码盘点快速确认了该资产所在。"
    )
    db.add(log_entry)
    db.commit()
    return log_entry

def update_asset_status(db: Session, asset_id: str, status: str, user_id: int):
    db_asset = get_asset(db, str(asset_id))
    if not db_asset:
        return None
        
    # [业务红线]：变为“在用”必须有人员，否则报错
    if status == "在用" and not db_asset.owner_id:
        raise ValueError("资产变更为'在用'状态时，必须先行关联使用人。")
        
    old_status = db_asset.status
    old_owner_id = db_asset.owner_id
    
    db_asset.status = status
    
    action = "Status Change"
    memo = f"通过移动端快速变更状态: [ {old_status} ] -> [ {status} ]"
    
    # 如果强制退库，一并清空名下人员与组织
    if status in ["闲置", "报废"]:
        db_asset.owner_id = None
        if db_asset.dynamic_attributes and "所属组织" in db_asset.dynamic_attributes:
            new_attrs = dict(db_asset.dynamic_attributes)
            new_attrs["所属组织"] = ""
            db_asset.dynamic_attributes = new_attrs
        action = "资产回收 (快捷状态修改)"
        memo = f"通过移动端强制退库，清空借用状态。"
    
    # 记录状态变更日志
    log_entry = AssetLog(
        asset_id=db_asset.id,
        operated_by=user_id,
        action=action,
        previous_owner_id=old_owner_id,
        new_owner_id=db_asset.owner_id,
        memo=memo
    )
    db.add(log_entry)
    db.commit()
    db.refresh(db_asset)
    return db_asset

def reassign_asset(db: Session, asset_id: str, new_owner_id: int, user_id: int):
    db_asset = get_asset(db, str(asset_id))
    if not db_asset:
        return None
    
    old_owner_name = db_asset.owner.name if db_asset.owner else "无"
    old_owner_id = db_asset.owner_id
    
    # fetch new owner name for log
    new_owner = db.query(Employee).filter(Employee.id == new_owner_id).first()
    new_owner_name = new_owner.name if new_owner else "无"
    
    # 方案 A 联动：如果资产是闲置状态，分配人员后自动变为“在用”
    if db_asset.status == "闲置":
        db_asset.status = "在用"
        
    db_asset.owner_id = new_owner_id
    
    log_entry = AssetLog(
        asset_id=db_asset.id,
        operated_by=user_id,
        action="Reassign",
        previous_owner_id=old_owner_id,
        new_owner_id=new_owner_id,
        memo=f"通过移动端快速调拨: [ {old_owner_name} ] -> [ {new_owner_name} ]"
    )
    db.add(log_entry)
    db.commit()
    db.refresh(db_asset)
    return db_asset

def get_employees(db: Session, skip: int = 0, limit: int = 10000, keyword: str = ""):
    return db.query(Employee).offset(skip).limit(limit).all()

def create_employee(db: Session, employee: EmployeeCreate):
    db_emp = Employee(**employee.dict())
    db.add(db_emp)
    db.commit()
    db.refresh(db_emp)
    return db_emp

# ====== Category CRUD ======
def get_categories(db: Session, skip: int = 0, limit: int = 10000):
    return db.query(Category).offset(skip).limit(limit).all()

def create_category(db: Session, category: CategoryCreate):
    db_cat = Category(**category.dict())
    db.add(db_cat)
    db.commit()
    db.refresh(db_cat)
    return db_cat

def update_category(db: Session, category_id: int, category_in: CategoryUpdate):
    db_cat = db.query(Category).filter(Category.id == category_id).first()
    if not db_cat:
        return None
        
    update_data = category_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_cat, field, value)
        
    db.add(db_cat)
    db.commit()
    db.refresh(db_cat)
    return db_cat

def delete_category(db: Session, category_id: int):
    db_cat = db.query(Category).filter(Category.id == category_id).first()
    if not db_cat:
        return False
    # Only allow deletion if no assets are linked to it (optional, but good practice).
    # Since sqlite/foreign keys handle this, we just try to delete.
    db.delete(db_cat)
    db.commit()
    return True

# ====== Asset CRUD ======
def get_assets(db: Session, skip: int = 0, limit: int = 10000, keyword: str = "", status: str = "", sort_by: str = "updated_at", order: str = "desc"):
    query = db.query(Asset).options(
        joinedload(Asset.category),
        joinedload(Asset.owner)
    )
    
    # 动态排序逻辑
    sort_col = getattr(Asset, sort_by, Asset.updated_at)
    if order == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())
    
    if keyword:
        from sqlalchemy import String
        search = f"%{keyword}%"
        # 搜索资产编码、分类名称、员工姓名或动态属性
        query = query.join(Category, isouter=True).join(Employee, isouter=True).filter(
            (Asset.asset_code.ilike(search)) |
            (Category.name.ilike(search)) |
            (Employee.name.ilike(search)) |
            (Asset.dynamic_attributes.cast(String).ilike(search))
        )
    
    if status:
        query = query.filter(Asset.status == status)
        
    return query.offset(skip).limit(limit).all()

def count_assets(db: Session, keyword: str = "", status: str = ""):
    query = db.query(Asset)
    
    if keyword:
        from sqlalchemy import String
        search = f"%{keyword}%"
        query = query.join(Category, isouter=True).join(Employee, isouter=True).filter(
            (Asset.asset_code.ilike(search)) |
            (Category.name.ilike(search)) |
            (Employee.name.ilike(search)) |
            (Asset.dynamic_attributes.cast(String).ilike(search))
        )
    
    if status:
        query = query.filter(Asset.status == status)
        
    return query.count()

def get_asset(db: Session, asset_id: str):
    asset_id_hex = asset_id.replace('-', '')
    return db.query(Asset).options(
        joinedload(Asset.category),
        joinedload(Asset.owner)
    ).filter((Asset.id == asset_id) | (Asset.id == asset_id_hex)).first()

def create_asset(db: Session, asset: AssetCreate, current_user_id: int):
    # 生成安全的 QR 鉴权 Token
    qr_token = str(uuid.uuid4().hex)
    
    db_asset = Asset(
        **asset.dict(),
        qr_code_token=qr_token
    )
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    
    # 记录日志
    log = AssetLog(
        asset_id=db_asset.id,
        operated_by=current_user_id,
        action="新建入库",
        new_owner_id=db_asset.owner_id,
        memo="资产初始录入"
    )
    db.add(log)
    db.commit()
    
    return db_asset

def update_asset(db: Session, asset_id: str, asset_in: AssetUpdate, current_user_id: int):
    db_asset = get_asset(db, asset_id)
    if not db_asset:
        return None
    
    update_data = asset_in.dict(exclude_unset=True)
    
    # 检测拥有者变更或状态变更记录志
    old_owner_id = db_asset.owner_id
    old_status = db_asset.status
    
    # 强制归还逻辑：如果状态变更为闲置或报废，清空使用人和部门
    new_status = update_data.get("status", old_status)
    new_owner_id = update_data.get("owner_id", old_owner_id)

    # [业务红线]：变为“在用”必须有人员，否则报错
    if new_status == "在用" and not new_owner_id:
        raise ValueError("资产变更为'在用'状态时，必须指定使用人。")

    if new_status in ["闲置", "报废"]:
        update_data["owner_id"] = None
        if "dynamic_attributes" in update_data and "所属组织" in update_data["dynamic_attributes"]:
            new_attrs = dict(update_data.get("dynamic_attributes") or db_asset.dynamic_attributes or {})
            new_attrs["所属组织"] = ""
            update_data["dynamic_attributes"] = new_attrs
            
    action = "信息更新"
    if old_owner_id != new_owner_id:
        if new_owner_id is None:
            action = "资产回收"
        elif old_owner_id is None:
            action = "资产派发"
        else:
            action = "资产调拨"
    elif old_status != new_status:
        action = f"状态变更 ({old_status} -> {new_status})"

    # --- 核心改进：人员变更时，强制同步域控中的组织单位到资产属性中 ---
    if new_owner_id:
        from models.asset import Employee
        emp = db.query(Employee).filter(Employee.id == new_owner_id).first()
        if emp and emp.department:
            if "dynamic_attributes" not in update_data:
                update_data["dynamic_attributes"] = dict(db_asset.dynamic_attributes or {})
            # 如果没有明确传所属组织，或者需要强制对齐，则更新
            update_data["dynamic_attributes"]["所属组织"] = emp.department
    # -------------------------------------------------------
        
    for field, value in update_data.items():
        # Specifically allow None for owner_id to clear it
        setattr(db_asset, field, value)
        
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    
    if action != "信息更新":
        log = AssetLog(
            asset_id=db_asset.id,
            operated_by=current_user_id,
            action=action,
            previous_owner_id=old_owner_id,
            new_owner_id=new_owner_id,
            memo=f"触发动作: {action}"
        )
        db.add(log)
        db.commit()
        
    return db_asset

def delete_asset(db: Session, asset_id: str, current_user_id: int):
    db_asset = get_asset(db, asset_id)
    if not db_asset:
        return None
        
    # 我们此处执行软删除（标记报废）以保持日志健全，不真删
    db_asset.status = "报废"
    db.add(db_asset)
    
    log = AssetLog(
        asset_id=db_asset.id,
        operated_by=current_user_id,
        action="报废/归档",
        previous_owner_id=db_asset.owner_id,
        new_owner_id=None,
        memo="执行软删除操作"
    )
    db.add(log)
    db.commit()
    db.refresh(db_asset)
    return db_asset

def hard_delete_asset(db: Session, asset_id: str):
    db_asset = get_asset(db, asset_id)
    if not db_asset:
        return False
        
    # Cascade logs deletion manually if needed, or rely on cascading in models
    db.query(AssetLog).filter(AssetLog.asset_id == db_asset.id).delete()
    db.delete(db_asset)
    db.commit()
    return True

def get_asset_logs(db: Session, asset_id: UUID):
    str_id = str(asset_id)
    hex_id = str_id.replace('-', '')
    logs = db.query(AssetLog).filter((AssetLog.asset_id == str_id) | (AssetLog.asset_id == hex_id)).order_by(AssetLog.created_at.desc()).all()
    
    for log in logs:
        operator = db.query(User).filter(User.id == log.operated_by).first()
        log.operator_name = operator.username if operator else "System"
        
        if log.previous_owner_id:
            prev_owner = db.query(Employee).filter(Employee.id == log.previous_owner_id).first()
            log.previous_owner_name = prev_owner.name if prev_owner else None
            
        if log.new_owner_id:
            new_owner = db.query(Employee).filter(Employee.id == log.new_owner_id).first()
            log.new_owner_name = new_owner.name if new_owner else None
            
    return logs
