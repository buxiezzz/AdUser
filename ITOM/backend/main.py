from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.requests import Request

from database import engine, SessionLocal
from models import user as user_model
from models import asset as asset_model
from models import audit as audit_model
from crud.user import get_user_by_username, create_user
from schemas.user import UserCreate
from api.routers import auth, asset, ad, settings, audit, inventory, location, transfer, user as user_router, stats

# Create database tables (For production use Alembic migrations instead)
user_model.Base.metadata.create_all(bind=engine)
asset_model.Base.metadata.create_all(bind=engine)
audit_model.Base.metadata.create_all(bind=engine)

# 强制确保盘点模块的新表存在（兼容旧数据库文件不包含这两张表的情况）
from models.asset import InventoryTask, InventoryRecord
from sqlalchemy import inspect as sa_inspect
_inspector = sa_inspect(engine)
_existing_tables = _inspector.get_table_names()
if "inventory_tasks" not in _existing_tables:
    InventoryTask.__table__.create(bind=engine, checkfirst=True)
    print("✅ 自动创建表: inventory_tasks")
if "inventory_records" not in _existing_tables:
    InventoryRecord.__table__.create(bind=engine, checkfirst=True)
    print("✅ 自动创建表: inventory_records")

# 确保归属地表存在
from models.asset import Location
if "locations" not in _existing_tables:
    Location.__table__.create(bind=engine, checkfirst=True)
    print("✅ 自动创建表: locations")

# 确保调拨表存在
from models.asset import AssetTransfer
if "asset_transfers" not in _existing_tables:
    AssetTransfer.__table__.create(bind=engine, checkfirst=True)
    print("✅ 自动创建表: asset_transfers")

# 确保新增字段存在（兼容旧数据库）
from sqlalchemy import text as sa_text
try:
    with engine.connect() as conn:
        # 检查 assets 表是否有 location_id 字段
        result = conn.execute(sa_text("PRAGMA table_info(assets)"))
        asset_columns = [row[1] for row in result.fetchall()]
        if "location_id" not in asset_columns:
            conn.execute(sa_text("ALTER TABLE assets ADD COLUMN location_id INTEGER REFERENCES locations(id)"))
            conn.commit()
            print("✅ 自动追加字段: assets.location_id")

        # 检查 employees 表是否有 location_id 字段
        result = conn.execute(sa_text("PRAGMA table_info(employees)"))
        emp_columns = [row[1] for row in result.fetchall()]
        if "location_id" not in emp_columns:
            conn.execute(sa_text("ALTER TABLE employees ADD COLUMN location_id INTEGER REFERENCES locations(id)"))
            conn.commit()
            print("✅ 自动追加字段: employees.location_id")

        # 检查 sys_users 表是否有 location_id 和 is_group_admin 字段
        result = conn.execute(sa_text("PRAGMA table_info(sys_users)"))
        user_columns = [row[1] for row in result.fetchall()]
        if "location_id" not in user_columns:
            conn.execute(sa_text("ALTER TABLE sys_users ADD COLUMN location_id INTEGER REFERENCES locations(id)"))
            conn.commit()
            print("✅ 自动追加字段: sys_users.location_id")
        if "is_group_admin" not in user_columns:
            conn.execute(sa_text("ALTER TABLE sys_users ADD COLUMN is_group_admin BOOLEAN DEFAULT 0"))
            conn.commit()
            print("✅ 自动追加字段: sys_users.is_group_admin")
        if "display_name" not in user_columns:
            conn.execute(sa_text("ALTER TABLE sys_users ADD COLUMN display_name VARCHAR(100)"))
            conn.commit()
            print("✅ 自动追加字段: sys_users.display_name")

        # 检查 sys_audit_logs 表是否有 device_source 字段
        result = conn.execute(sa_text("PRAGMA table_info(sys_audit_logs)"))
        audit_columns = [row[1] for row in result.fetchall()]
        if "device_source" not in audit_columns:
            conn.execute(sa_text("ALTER TABLE sys_audit_logs ADD COLUMN device_source VARCHAR(20)"))
            conn.commit()
            print("✅ 自动追加字段: sys_audit_logs.device_source")

        # 检查 inventory_tasks 表是否有 location_id 字段
        result = conn.execute(sa_text("PRAGMA table_info(inventory_tasks)"))
        task_columns = [row[1] for row in result.fetchall()]
        if "location_id" not in task_columns:
            conn.execute(sa_text("ALTER TABLE inventory_tasks ADD COLUMN location_id INTEGER REFERENCES locations(id)"))
            conn.commit()
            print("✅ 自动追加字段: inventory_tasks.location_id")
except Exception as e:
    print(f"⚠️ 数据库迁移警告: {e}")

app = FastAPI(
    title="ITOM Platform API",
    description="Comprehensive IT Operations Management Platform",
    version="1.0.0"
)

# 配置 CORS，允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境请修改为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(asset.router, prefix="/api/assets", tags=["Assets"])
app.include_router(ad.router, prefix="/api/ad", tags=["Active Directory"])
app.include_router(settings.router, prefix="/api/settings", tags=["System Settings"])
app.include_router(audit.router, prefix="/api/audit", tags=["Audit Logs"])
app.include_router(inventory.router, prefix="/api/inventory", tags=["Inventory Management"])
app.include_router(location.router, prefix="/api/locations", tags=["Location Management"])
app.include_router(transfer.router, prefix="/api/transfers", tags=["Asset Transfer Management"])
app.include_router(user_router.router, prefix="/api/users", tags=["User Management"])
app.include_router(stats.router, prefix="/api/stats", tags=["Statistics"])

@app.on_event("startup")
def create_default_admin():
    db = SessionLocal()
    try:
        admin_user = get_user_by_username(db, username="admin")
        if not admin_user:
            print("System Initialization: Creating default administrator account...")
            default_admin = UserCreate(
                username="admin",
                password="admin123",
                role="admin"
            )
            admin_user = create_user(db, default_admin)
            print("Default admin created successfully! User: admin / Pass: admin123")
        
        # 确保 admin 用户升级为集团超管
        if not admin_user.is_group_admin:
            admin_user.is_group_admin = True
            db.commit()
            print("✅ admin 用户已升级为集团超管")
        
        # 初始化默认归属地数据
        from models.asset import Location
        existing_locations = db.query(Location).count()
        if existing_locations == 0:
            default_locations = [
                Location(code="SH", name="上海总部", address="上海市"),
                Location(code="WH", name="武汉分公司", address="武汉市"),
                Location(code="CS", name="长沙分公司", address="长沙市"),
            ]
            for loc in default_locations:
                db.add(loc)
            db.commit()
            print("✅ 已初始化默认归属地: 上海总部、武汉分公司、长沙分公司")
    finally:
        db.close()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"Validation Error Request Body: {await request.body()}")
    print(f"Errors: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": str(exc.body)},
    )

@app.get("/")
def read_root():
    return {"message": "Welcome to ITOM Platform API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
