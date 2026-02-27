from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any, Dict
from pydantic import BaseModel
import json
import os
import ssl
from ldap3 import Server, Connection, Tls
from api.deps import get_current_active_user

router = APIRouter()
# os.path.dirname(__file__) is <backend>/api/routers
# os.path.dirname(...) twice goes to <backend>
CONFIG_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'core', 'config.json')

class SettingsUpdateSchema(BaseModel):
    domain_controller_ip: str | None = None
    domain_name: str | None = None
    bind_username: str | None = None
    bind_password: str | None = None
    default_user_password: str | None = None
    allow_registration: bool | None = None
    audit_log: bool | None = None
    positions: list[dict] | None = None
    region_options: list[dict] | None = None
    active_region_code: str | None = None

def load_config() -> Dict[str, Any]:
    if not os.path.exists(CONFIG_FILE_PATH):
        return {
            "DOMAIN_CONTROLLER_IP": "",
            "DOMAIN_NAME": "your_domain.com",
            "BIND_USERNAME": "",
            "BIND_PASSWORD": "",
            "DEFAULT_USER_PASSWORD": "ChangeMePlease123!",
            "ALLOW_REGISTRATION": True,
            "AUDIT_LOG": True,
            "POSITIONS": [
                {"name": "Developer", "suffix": "dev"},
                {"name": "Manager", "suffix": "mgr"}
            ],
            "REGION_OPTIONS": [],
            "ACTIVE_REGION_CODE": "all"
        }
    with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_config(config_data: Dict[str, Any]):
    with open(CONFIG_FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)


@router.get("/public", response_model=Dict[str, Any])
def get_public_settings():
    """获取公开的系统级设定 (如是否允许注册)"""
    config_data = load_config()
    return {
        "allow_registration": config_data.get("ALLOW_REGISTRATION", True)
    }

@router.get("/", response_model=Dict[str, Any])
def get_settings(current_user: Any = Depends(get_current_active_user)):
    """获取系统基础配置项"""
    # 出于安全考虑，通常不向前端直接暴露某些密码信息，不过这是 Admin 级别的 API 
    # 可以视需求做脱敏
    config_data = load_config()
    return config_data


@router.post("/", response_model=Dict[str, Any])
def update_settings(
    settings: SettingsUpdateSchema,
    current_user: Any = Depends(get_current_active_user)
):
    """更新系统级配置"""
    if current_user.role != 'admin':  # 只有超管可配
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，仅超级管理员可修改全局系统设定"
        )
        
    config_data = load_config()
    
    if settings.domain_controller_ip is not None:
        config_data["DOMAIN_CONTROLLER_IP"] = settings.domain_controller_ip
    if settings.domain_name is not None:
        config_data["DOMAIN_NAME"] = settings.domain_name
    if settings.bind_username is not None:
        config_data["BIND_USERNAME"] = settings.bind_username
    if settings.bind_password is not None:
        config_data["BIND_PASSWORD"] = settings.bind_password
    if settings.default_user_password is not None:
         config_data["DEFAULT_USER_PASSWORD"] = settings.default_user_password   
         
    # Registration Security Toggle
    if settings.allow_registration is not None:
        config_data["ALLOW_REGISTRATION"] = settings.allow_registration
    if settings.audit_log is not None:
        config_data["AUDIT_LOG"] = settings.audit_log
        
    # Positions and Rules
    if settings.positions is not None:
        config_data["POSITIONS"] = settings.positions
    if settings.region_options is not None:
        config_data["REGION_OPTIONS"] = settings.region_options
    if settings.active_region_code is not None:
        config_data["ACTIVE_REGION_CODE"] = settings.active_region_code
        
    save_config(config_data)
    
    return {"success": True, "message": "全局配置更新成功", "data": config_data}

class ADTestSchema(BaseModel):
    dc_ip: str
    username: str
    password: str

@router.post("/test-ad", response_model=Dict[str, Any])
def test_ad_connection_live(
    req: ADTestSchema,
    current_user: Any = Depends(get_current_active_user)
):
    """测试真实的 AD 域控连通性"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权进行AD测试")
    
    try:
        tls_config = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLS_CLIENT)
        server = Server(req.dc_ip, port=636, use_ssl=True, tls=tls_config)
        conn = Connection(server, user=req.username, password=req.password, auto_bind=True)
        if conn.bound:
            conn.unbind()
            return {"success": True, "message": "成功探测到 AD 域控并完成身份验证！"}
        else:
            raise HTTPException(status_code=400, detail=f"AD 返回拒绝: {conn.result}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"AD 连接或验证失败: {str(e)}")
