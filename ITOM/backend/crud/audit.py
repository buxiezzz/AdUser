from sqlalchemy.orm import Session
from models.audit import AuditLog
import json

def log_action(db: Session, username: str, module: str, action: str, target: str, details: dict = None, ip_address: str = None, device_source: str = None):
    """
    统一审计日志记录器
    :param db: 数据库会话
    :param username: 操作人姓名 (从 Token 提取)
    :param module: 模块名称 (如 'asset', 'ad')
    :param action: 操作类型 (如 'CREATE', 'UPDATE', 'DELETE')
    :param target: 目标资源唯一标识 (如 资产号 或 用户名)
    :param details: 额外变动详情 (JSON 可序列化对象)
    :param device_source: 终端来源 (如 '📱手机端', '💻电脑端')
    """
    detail_str = json.dumps(details, ensure_ascii=False) if details else ""
    db_log = AuditLog(
        username=username,
        module=module,
        action=action,
        target=target,
        details=detail_str,
        ip_address=ip_address,
        device_source=device_source
    )
    db.add(db_log)
    db.commit()
    return db_log

def get_logs(db: Session, module: str = None, skip: int = 0, limit: int = 100):
    query = db.query(AuditLog)
    if module:
        query = query.filter(AuditLog.module == module)
    return query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()

def count_logs(db: Session, module: str = None):
    query = db.query(AuditLog)
    if module:
        query = query.filter(AuditLog.module == module)
    return query.count()
