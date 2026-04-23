import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uuid
from datetime import datetime
import pytz
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from database import Base

# 获取北京时间的辅助函数
def get_beijing_time():
    return datetime.now(pytz.timezone('Asia/Shanghai'))

# 归属地模型：集团下的子公司/分部
class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False)       # 归属地编码，如 "SH", "WH", "CS"
    name = Column(String(100), unique=True, nullable=False)      # 归属地名称，如 "上海总部"
    address = Column(String(255), nullable=True)                 # 详细地址
    contact_person = Column(String(50), nullable=True)           # 负责人
    contact_phone = Column(String(20), nullable=True)            # 联系电话
    is_active = Column(Boolean, default=True)                    # 是否启用
    created_at = Column(DateTime, default=get_beijing_time)

class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    department = Column(String(100))
    email = Column(String(100), unique=True, index=True)
    ad_account = Column(String(50), unique=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)  # 员工归属地
    created_at = Column(DateTime, default=get_beijing_time)
    
    # 关系
    assets = relationship("Asset", back_populates="owner")
    location = relationship("Location")

class Category(Base):
    __tablename__ = "asset_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False) # e.g., 笔记本, 显示器, 交换机
    default_attributes = Column(JSON, default={}) # 用于前端渲染该类别默认需要填哪些字段

    assets = relationship("Asset", back_populates="category")

class Asset(Base):
    __tablename__ = "assets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    asset_code = Column(String(100), unique=True, index=True) # 财务固资编号
    category_id = Column(Integer, ForeignKey("asset_categories.id"))
    status = Column(String(20), default="闲置") # 闲置, 在用, 维修, 报废, 下账
    owner_id = Column(Integer, ForeignKey("employees.id"), nullable=True) # 当前使用者
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)  # 资产归属地
    
    dynamic_attributes = Column(JSON, default={}) # 核心动态属性，存储 MAC、IP、CPU 等任意字段
    qr_code_token = Column(String(255), unique=True, nullable=True) # 用于H5扫码鉴权的独立票据
    
    created_at = Column(DateTime, default=get_beijing_time)
    updated_at = Column(DateTime, default=get_beijing_time, onupdate=get_beijing_time)

    owner = relationship("Employee", back_populates="assets")
    category = relationship("Category", back_populates="assets")
    location = relationship("Location")
    logs = relationship("AssetLog", back_populates="asset")
    transfers = relationship("AssetTransfer", back_populates="asset")

class AssetLog(Base):
    __tablename__ = "asset_logs"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String(36), ForeignKey("assets.id"))
    operated_by = Column(Integer, ForeignKey("sys_users.id")) # 操作的系统管理员
    action = Column(String(50)) # 如下发、回收、维修
    previous_owner_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    new_owner_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    memo = Column(Text, nullable=True) # 备注
    created_at = Column(DateTime, default=get_beijing_time)

    asset = relationship("Asset", back_populates="logs")

class InventoryTask(Base):
    __tablename__ = "inventory_tasks"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), index=True)
    description = Column(String(255), nullable=True)
    start_time = Column(DateTime, default=get_beijing_time)
    end_time = Column(DateTime, nullable=True)
    status = Column(String(20), default="进行中")  # 进行中, 已完成, 已取消
    total_count = Column(Integer, default=0)
    finished_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=get_beijing_time)
    
    records = relationship("InventoryRecord", back_populates="task")

class InventoryRecord(Base):
    __tablename__ = "inventory_records"
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(36), ForeignKey("inventory_tasks.id"))
    asset_id = Column(String(36), ForeignKey("assets.id"))
    status = Column(String(20), default="未盘点")  # 未盘点, 已盘点, 盘亏
    audit_time = Column(DateTime, nullable=True)
    operator_id = Column(Integer, ForeignKey("sys_users.id"), nullable=True)
    
    task = relationship("InventoryTask", back_populates="records")
    asset = relationship("Asset")

class AssetTransfer(Base):
    __tablename__ = "asset_transfers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    asset_id = Column(String(36), ForeignKey("assets.id"))
    from_location_id = Column(Integer, ForeignKey("locations.id"))
    to_location_id = Column(Integer, ForeignKey("locations.id"))
    
    # 待审批, 待发货, 运输中, 已完成, 已拒绝
    status = Column(String(20), default="待审批")
    
    applicant_id = Column(Integer, ForeignKey("sys_users.id"))
    approver_id = Column(Integer, ForeignKey("sys_users.id"), nullable=True)
    
    memo = Column(Text, nullable=True)
    tracking_number = Column(String(100), nullable=True) # 物流单号
    
    created_at = Column(DateTime, default=get_beijing_time)
    updated_at = Column(DateTime, default=get_beijing_time, onupdate=get_beijing_time)

    # 关系
    asset = relationship("Asset")
    from_location = relationship("Location", foreign_keys=[from_location_id])
    to_location = relationship("Location", foreign_keys=[to_location_id])
    applicant = relationship("User", foreign_keys=[applicant_id])
    approver = relationship("User", foreign_keys=[approver_id])
