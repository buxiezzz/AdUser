from sqlalchemy.orm import Session
from models.asset import Location
from schemas.asset import LocationCreate, LocationUpdate


def get_locations(db: Session, include_inactive: bool = False):
    """获取所有归属地列表"""
    query = db.query(Location)
    if not include_inactive:
        query = query.filter(Location.is_active == True)
    return query.order_by(Location.id).all()


def get_location(db: Session, location_id: int):
    """根据ID获取归属地"""
    return db.query(Location).filter(Location.id == location_id).first()


def get_location_by_code(db: Session, code: str):
    """根据编码获取归属地"""
    return db.query(Location).filter(Location.code == code).first()


def create_location(db: Session, location: LocationCreate):
    """创建归属地"""
    db_loc = Location(**location.dict())
    db.add(db_loc)
    db.commit()
    db.refresh(db_loc)
    return db_loc


def update_location(db: Session, location_id: int, location_in: LocationUpdate):
    """更新归属地"""
    db_loc = db.query(Location).filter(Location.id == location_id).first()
    if not db_loc:
        return None

    update_data = location_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_loc, field, value)

    db.add(db_loc)
    db.commit()
    db.refresh(db_loc)
    return db_loc


def delete_location(db: Session, location_id: int):
    """删除归属地（软删除，标记为不活跃）"""
    db_loc = db.query(Location).filter(Location.id == location_id).first()
    if not db_loc:
        return False
    db_loc.is_active = False
    db.commit()
    return True
