import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uuid
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from database import Base

class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    department = Column(String(100))
    email = Column(String(100), unique=True, index=True)
    ad_account = Column(String(50), unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    assets = relationship("Asset", back_populates="owner")

class Category(Base):
    __tablename__ = "asset_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False) # e.g., 笔记本, 显示器, 交换机
    default_attributes = Column(JSONB, default={}) # 用于前端渲染该类别默认需要填哪些字段

    assets = relationship("Asset", back_populates="category")

class Asset(Base):
    __tablename__ = "assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_code = Column(String(100), unique=True, index=True) # 财务固资编号
    category_id = Column(Integer, ForeignKey("asset_categories.id"))
    status = Column(String(20), default="在库") # 在库, 借用中, 维修中, 报废
    owner_id = Column(Integer, ForeignKey("employees.id"), nullable=True) # 当前使用者
    
    dynamic_attributes = Column(JSONB, default={}) # 核心动态属性，存储 MAC、IP、CPU 等任意字段
    qr_code_token = Column(String(255), unique=True, nullable=True) # 用于H5扫码鉴权的独立票据
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("Employee", back_populates="assets")
    category = relationship("Category", back_populates="assets")
    logs = relationship("AssetLog", back_populates="asset")

class AssetLog(Base):
    __tablename__ = "asset_logs"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"))
    operated_by = Column(Integer, ForeignKey("sys_users.id")) # 操作的系统管理员
    action = Column(String(50)) # 如下发、回收、维修
    previous_owner_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    new_owner_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    memo = Column(Text, nullable=True) # 备注
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    asset = relationship("Asset", back_populates="logs")
