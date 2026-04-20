import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 优先从环境变量读取，默认使用 SQLite 方便本地直接运行测试
# 优先从环境变量读取，默认根据运行环境选择路径
# 如果在容器内（/app 存在），则存放在挂载的 /app/data 卷中
if os.path.exists("/app"):
    DEFAULT_DB = "sqlite:////app/data/itom.db"
else:
    DEFAULT_DB = "sqlite:///./itom_test.db"

DATABASE_URL = os.getenv("ITOM_DATABASE_URL", DEFAULT_DB)

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
