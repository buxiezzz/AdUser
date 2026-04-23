from database import SessionLocal
from models.user import User
from models.asset import Asset, AssetTransfer, Location
# 如果有其他关联模型如 Category, Employee，也建议导入以防万一
from api.routers.asset import Employee

def cleanup():
    db = SessionLocal()
    try:
        # 1. 查找所有未完成的调拨单
        transfers = db.query(AssetTransfer).filter(
            AssetTransfer.status.in_(["待审批", "待发货", "运输中"])
        ).all()
        
        count = 0
        for t in transfers:
            # 2. 检查关联资产是否存在
            asset = db.query(Asset).filter(Asset.id == t.asset_id).first()
            if not asset:
                # 3. 如果资产不存在，标记为“已取消”
                print(f"发现僵尸单据: ID={t.id}, 关联资产={t.asset_id} 不存在。正在标记为‘已取消’...")
                t.status = "已取消"
                t.memo = (t.memo or "") + " [系统自动清理：关联资产已不存在]"
                count += 1
        
        if count > 0:
            db.commit()
            print(f"清理完成，共处理 {count} 个僵尸单据。")
        else:
            print("未发现需要处理的僵尸单据。")
            
    finally:
        db.close()

if __name__ == "__main__":
    cleanup()
