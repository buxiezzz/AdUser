from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse, StreamingResponse
from typing import Any, Dict
from pydantic import BaseModel
import json
import os
import ssl
import zipfile
import io
from ldap3 import Server, Connection, Tls
from api.deps import get_current_active_user, get_device_source
import glob
from sqlalchemy.orm import Session
from database import DATABASE_URL, get_db
from crud.audit import log_action

router = APIRouter()

def get_base_data_dir() -> str:
    if os.path.exists("/app"):
        return "/app/data"
    else:
        return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'core')

def get_config_path(location_id=None) -> str:
    base_dir = get_base_data_dir()
    if location_id:
        return os.path.join(base_dir, f"config_location_{location_id}.json")
    return os.path.join(base_dir, "config.json")



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
    ou_group_mapping: Dict[str, list[str]] | None = None
    ou_prefix_mapping: Dict[str, str] | None = None
    print_template: dict | None = None

def load_config(location_id=None) -> Dict[str, Any]:
    config_path = get_config_path(location_id)
    if location_id and not os.path.exists(config_path):
        # Fallback to default if location specific config doesn't exist yet
        config_path = get_config_path(None)

        
    if not os.path.exists(config_path):
        return {
            "DOMAIN_CONTROLLER_IP": "",
            "DOMAIN_NAME": "your_domain.com",
            "BIND_USERNAME": "",
            "BIND_PASSWORD": "",
            "DEFAULT_USER_PASSWORD": "ChangeMePlease123!",
            "ALLOW_REGISTRATION": True,
            "AUDIT_LOG": True,
            "POSITIONS": [
                {"name": "Developer", "suffix": "dev", "default_groups": []},
                {"name": "Manager", "suffix": "mgr", "default_groups": []}
            ],
            "OU_GROUP_MAPPING": {},
            "OU_PREFIX_MAPPING": {},
            "REGION_OPTIONS": [],
            "ACTIVE_REGION_CODE": "all",
            "PRINT_TEMPLATE": {
                "width": 70,
                "height": 50,
                "padding": 2,
                "border": 2,
                "company_name": "先惠自动化技术(武汉)有限责任公司",
                "rows": {
                    "r1": 12, "r2": 8, "r3": 8, "r4": 8, "r5": 6, "r6": 6
                },
                "fonts": {
                    "title": 15, "code": 13, "name": 13, "spec": 13, "serial": 13, "date": 13
                },
                "leftColWidth": 62,
                "qrSize": 62
            }
        }
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_config(config_data: Dict[str, Any], location_id=None):
    config_path = get_config_path(location_id)
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)



@router.get("/public", response_model=Dict[str, Any])
def get_public_settings():
    """获取公开的系统级设定 (如是否允许注册)"""
    config_data = load_config(None)
    return {
        "allow_registration": config_data.get("ALLOW_REGISTRATION", True)
    }

@router.get("/", response_model=Dict[str, Any])
def get_settings(current_user: Any = Depends(get_current_active_user)):
    """获取系统基础配置项"""
    # 出于安全考虑，通常不向前端直接暴露某些密码信息，不过这是 Admin 级别的 API 
    # 可以视需求做脱敏
    config_data = load_config(current_user.location_id)
    return config_data



@router.post("/", response_model=Dict[str, Any])
def update_settings(
    settings: SettingsUpdateSchema,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_active_user),
    device: str = Depends(get_device_source)
):
    """更新系统级配置"""
    if current_user.role != 'admin':  # 只有超管可配
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，仅超级管理员可修改全局系统设定"
        )
        
    config_data = load_config(current_user.location_id)

    
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
    if settings.ou_group_mapping is not None:
        config_data["OU_GROUP_MAPPING"] = settings.ou_group_mapping
    if settings.ou_prefix_mapping is not None:
        config_data["OU_PREFIX_MAPPING"] = settings.ou_prefix_mapping
    if settings.print_template is not None:
        config_data["PRINT_TEMPLATE"] = settings.print_template
        
    save_config(config_data, current_user.location_id)
    log_action(db, (current_user.display_name or current_user.username), 'settings', 'UPDATE_SETTINGS', '全局系统配置', device_source=device)
    
    return {"success": True, "message": "全局配置更新成功", "data": config_data}

@router.get("/export")
def export_settings(current_user: Any = Depends(get_current_active_user)):
    """导出系统配置文件与数据库包"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限导出")
    
    base_dir = get_base_data_dir()
    default_config_path = get_config_path(None)
    if not os.path.exists(default_config_path):
        config_data = load_config(None)
        save_config(config_data, None)

    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        # 1. 写入所有的配置文件 config*.json
        config_files = glob.glob(os.path.join(base_dir, 'config*.json'))
        for c_file in config_files:
            zf.write(c_file, arcname=os.path.basename(c_file))
        
        # 2. 写入数据库文件
        if DATABASE_URL.startswith("sqlite:///"):
            db_path = DATABASE_URL.replace("sqlite:///", "")
            if os.path.exists(db_path):
                zf.write(db_path, arcname="itom.db")
                
    memory_file.seek(0)
    return StreamingResponse(
        memory_file,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=itom_backup.zip"}
    )

@router.post("/import")
def import_settings(
    file: UploadFile = File(...),
    current_user: Any = Depends(get_current_active_user)
):
    """导入系统配置文件或全量备份包，并立即生效"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限导入")
    
    if not (file.filename.endswith('.json') or file.filename.endswith('.zip')):
        raise HTTPException(status_code=400, detail="请上传 .json 或 .zip 格式的备份文件")

    try:
        content = file.file.read()
        
        # 兼容老逻辑：如果只传了 .json
        if file.filename.endswith('.json'):
            config_data = json.loads(content.decode('utf-8'))
            if not isinstance(config_data, dict):
                raise ValueError("配置文件格式错误：不是一个有效的字典结构")
            # 导入单文件只保存给现在的归属地
            save_config(config_data, current_user.location_id)
            return {"success": True, "message": "配置导入成功，已立即生效"}

            
        # 全量恢复逻辑：如果传了 .zip
        if file.filename.endswith('.zip'):
            base_dir = get_base_data_dir()
            with zipfile.ZipFile(io.BytesIO(content), 'r') as zf:
                # 恢复所有配置 config*.json
                for item_name in zf.namelist():
                    if item_name.startswith('config') and item_name.endswith('.json'):
                        config_data = json.loads(zf.read(item_name).decode('utf-8'))
                        if isinstance(config_data, dict):
                            out_path = os.path.join(base_dir, item_name)
                            with open(out_path, 'w', encoding='utf-8') as out_f:
                                json.dump(config_data, out_f, indent=2, ensure_ascii=False)
                
                # 恢复数据库
                if 'itom.db' in zf.namelist():
                    if DATABASE_URL.startswith("sqlite:///"):
                        db_path = DATABASE_URL.replace("sqlite:///", "")
                        with open(db_path, 'wb') as f:
                            f.write(zf.read('itom.db'))
                            
            return {"success": True, "message": "全栈系统备份已成功恢复！应用和数据库已加载至备份节点。"}
            
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="解析配置文件失败，非标准 JSON 格式")
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="ZIP 数据包已损坏")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入恢复失败: {str(e)}")

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

