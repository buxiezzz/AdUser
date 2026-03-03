from sqlalchemy.orm import Session
from uuid import UUID
import uuid

from models.asset import Asset, Category, Employee, AssetLog
from models.user import User
from schemas.asset import AssetCreate, AssetUpdate, CategoryCreate, CategoryUpdate, EmployeeCreate

# ====== Employee CRUD ======
def get_employees(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Employee).offset(skip).limit(limit).all()

def create_employee(db: Session, employee: EmployeeCreate):
    db_emp = Employee(**employee.dict())
    db.add(db_emp)
    db.commit()
    db.refresh(db_emp)
    return db_emp

# ====== Category CRUD ======
def get_categories(db: Session, skip: int = 0, limit: int = 100):
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
def get_assets(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Asset).offset(skip).limit(limit).all()

def get_asset(db: Session, asset_id: UUID):
    return db.query(Asset).filter(Asset.id == asset_id).first()

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

def update_asset(db: Session, asset_id: UUID, asset_in: AssetUpdate, current_user_id: int):
    db_asset = get_asset(db, asset_id)
    if not db_asset:
        return None
    
    update_data = asset_in.dict(exclude_unset=True)
    
    # 检测拥有者变更或状态变更记录志
    old_owner_id = db_asset.owner_id
    new_owner_id = update_data.get("owner_id", old_owner_id)
    old_status = db_asset.status
    new_status = update_data.get("status", old_status)
    
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
        
    for field, value in update_data.items():
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

def delete_asset(db: Session, asset_id: UUID, current_user_id: int):
    db_asset = get_asset(db, asset_id)
    if not db_asset:
        return None
        
    # 我们此处执行软删除（标记报废归档）以保持日志健全，不真删
    db_asset.status = "已归档/报废"
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

def hard_delete_asset(db: Session, asset_id: UUID):
    db_asset = get_asset(db, asset_id)
    if not db_asset:
        return False
        
    # Cascade logs deletion manually if needed, or rely on cascading in models
    db.query(AssetLog).filter(AssetLog.asset_id == asset_id).delete()
    db.delete(db_asset)
    db.commit()
    return True

def get_asset_logs(db: Session, asset_id: UUID):
    logs = db.query(AssetLog).filter(AssetLog.asset_id == asset_id).order_by(AssetLog.created_at.desc()).all()
    
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
