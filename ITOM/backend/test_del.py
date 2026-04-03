from database import SessionLocal
from crud.asset import get_asset, hard_delete_asset
from models.user import User

db = SessionLocal()
try:
    print("Testing get_asset")
    asset = get_asset(db, "0024b80919d34d3bba9f7741d7616296")
    if asset:
        print(f"Asset found: {asset.id}")
        # Test hard delete logs (this happens inside hard_delete_asset)
        hard_delete_asset(db, str(asset.id))
        print("Hard delete executed.")
    else:
        print("Asset not found")
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    db.close()
