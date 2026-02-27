from sqlalchemy.orm import Session
from uuid import UUID
import uuid

from models.asset import Asset, Category, Employee, AssetLog
from schemas.asset import AssetCreate, AssetUpdate, CategoryCreate, EmployeeCreate

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
