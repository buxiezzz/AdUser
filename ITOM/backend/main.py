from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.requests import Request

from database import engine, SessionLocal
from models import user as user_model
from models import asset as asset_model
from crud.user import get_user_by_username, create_user
from schemas.user import UserCreate
from api.routers import auth, asset, ad, settings

# Create database tables (For production use Alembic migrations instead)
user_model.Base.metadata.create_all(bind=engine)
asset_model.Base.metadata.create_all(bind=engine)

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
            create_user(db, default_admin)
            print("Default admin created successfully! User: admin / Pass: admin123")
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
