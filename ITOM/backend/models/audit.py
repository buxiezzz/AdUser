from sqlalchemy import Column, Integer, String, Text, DateTime
from database import Base
from datetime import datetime
import pytz

# 获取北京时间的辅助函数 (与 asset 模型保持一致)
def get_beijing_time():
    return datetime.now(pytz.timezone('Asia/Shanghai'))

class AuditLog(Base):
    __tablename__ = "sys_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), index=True) # 操作者
    module = Column(String(20), index=True)   # 模型: 'asset', 'ad'
    action = Column(String(50))               # 动作: 'CREATE', 'UPDATE', 'DELETE', 'PROVISION'
    target = Column(String(100), index=True) # 目标标识: 资产号 或 姓名
    details = Column(Text)                    # 变动明细 (JSON)
    ip_address = Column(String(50), nullable=True) # 操作 IP
    device_source = Column(String(20), nullable=True) # 终端来源: '📱手机端' 或 '💻电脑端'
    created_at = Column(DateTime, default=get_beijing_time)
