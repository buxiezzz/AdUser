from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import pytz

from database import get_db
from models.asset import Asset, Category, AssetLog
from models.audit import AuditLog
from api.deps import get_current_active_user
from models.user import User

router = APIRouter()

def get_beijing_time():
    return datetime.now(pytz.timezone('Asia/Shanghai'))

@router.get("/dashboard")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    from models.asset import Location
    
    # 权限隔离逻辑: 如果不是集团管理员，强制锁定在其归属地
    effective_location_id = None
    if not current_user.is_group_admin:
        effective_location_id = current_user.location_id
    
    # 构建基础查询过滤器
    def apply_filter(query, model):
        if effective_location_id:
            return query.filter(model.location_id == effective_location_id)
        return query

    # 1. Overall Counts
    total_assets = apply_filter(db.query(Asset), Asset).count()
    idle_assets = apply_filter(db.query(Asset).filter(Asset.status == "闲置"), Asset).count()
    error_assets = apply_filter(db.query(Asset).filter(Asset.status == "维修"), Asset).count()
    
    # 2. Asset Distribution by Category
    cat_query = db.query(Category.name, func.count(Asset.id)).join(Asset)
    cat_query = apply_filter(cat_query, Asset)
    category_dist = cat_query.group_by(Category.name).all()
    category_data = [{"name": name, "value": count} for name, count in category_dist]
    
    # 3. Last 7 Days Activity Trend (Filtered by location via user logs if possible, else global)
    end_date = get_beijing_time().date()
    start_date = end_date - timedelta(days=6)
    dates = []
    trend_data = []
    transfer_trend_data = []
    
    for i in range(7):
        curr_date = start_date + timedelta(days=i)
        dates.append(curr_date.strftime("%m-%d"))
        
        # 1. 系统操作审计记录 (AuditLog)
        audit_count = db.query(AuditLog).filter(func.date(AuditLog.created_at) == str(curr_date)).count()
        trend_data.append(audit_count)
        
        # 2. 资产实际流转记录 (AssetLog)
        transfer_count = db.query(AssetLog).filter(func.date(AssetLog.created_at) == str(curr_date)).count()
        transfer_trend_data.append(transfer_count)

    # 4. Multi-Location Comparison (Only for Super Admins)
    location_data = []
    if current_user.is_group_admin:
        loc_dist = db.query(Location.name, func.count(Asset.id)).join(Asset, isouter=True).group_by(Location.name).all()
        location_data = [{"name": name if name else "未分配", "value": count} for name, count in loc_dist]

    return {
        "is_group_admin": current_user.is_group_admin,
        "counts": {
            "total": total_assets,
            "idle": idle_assets,
            "error": error_assets
        },
        "category_dist": category_data,
        "location_dist": location_data,
        "trend": {
            "dates": dates,
            "values": trend_data,
            "transfers": transfer_trend_data
        }
    }
