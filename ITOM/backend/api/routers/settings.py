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

# 全局统一字段：所有区域共享，只能由 admin 修改，以 config.json 为唯一真实来源
GLOBAL_KEYS = {
    "DOMAIN_CONTROLLER_IP", "DOMAIN_NAME", "BIND_USERNAME", "BIND_PASSWORD",
    "DEFAULT_USER_PASSWORD", "ALLOW_REGISTRATION", "AUDIT_LOG", "REGION_OPTIONS"
}

# 区域独立字段：每个分公司可拥有自己的配置
LOCAL_KEYS = {
    "POSITIONS", "OU_GROUP_MAPPING", "OU_PREFIX_MAPPING",
    "ACTIVE_REGION_CODE", "DEFAULT_USER_PASSWORD", "PRINT_TEMPLATE"
}

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

def is_super_admin(user) -> bool:
    """判断是否为系统超级管理员（仅 admin 账号）"""
    return user.username == 'admin'



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

def _read_json_file(path: str) -> Dict[str, Any]:
    """安全读取 JSON 配置文件"""
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def _default_config() -> Dict[str, Any]:
    """系统出厂默认配置"""
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

def load_config(location_id=None) -> Dict[str, Any]:
    """
    合并加载配置：
    - 全局字段（域控IP、绑定账号等）始终从 config.json 读取，保证全局统一
    - 区域独立字段（岗位、OU映射等）从 config_location_X.json 覆盖
    """
    global_path = get_config_path(None)
    global_data = _read_json_file(global_path)
    
    if not global_data:
        global_data = _default_config()
    
    # 无区域或就是全局请求，直接返回
    if not location_id:
        return global_data
    
    # 有区域：读取区域文件，用区域独立字段覆盖全局基准
    local_path = get_config_path(location_id)
    local_data = _read_json_file(local_path)
    
    if not local_data:
        # 区域文件不存在，回退到全局配置
        return global_data
    
    # 合并策略：以全局文件的全局字段为准，区域字段用区域文件覆盖
    merged = dict(global_data)  # 以全局为底
    for key in LOCAL_KEYS:
        if key in local_data:
            merged[key] = local_data[key]
    
    return merged

def save_config(config_data: Dict[str, Any], location_id=None):
    config_path = get_config_path(location_id)
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)

def sync_global_to_all_locations(global_data: Dict[str, Any]):
    """
    将全局字段同步写入所有已存在的区域配置文件。
    保留每个区域文件自身的区域独立字段不变。
    """
    base_dir = get_base_data_dir()
    for fname in os.listdir(base_dir):
        if fname.startswith('config_location_') and fname.endswith('.json'):
            loc_path = os.path.join(base_dir, fname)
            try:
                loc_data = _read_json_file(loc_path)
                if not loc_data:
                    continue
                # 用最新的全局字段覆盖区域文件中的对应字段
                for key in GLOBAL_KEYS:
                    if key in global_data:
                        loc_data[key] = global_data[key]
                with open(loc_path, 'w', encoding='utf-8') as f:
                    json.dump(loc_data, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"⚠️ 同步全局配置到 {fname} 失败: {e}")


def sync_local_to_all_locations(local_data: Dict[str, Any]):
    """
    将 admin 在全局修改的区域独立字段，强制同步广播写入所有已存在的区域配置文件中。
    """
    base_dir = get_base_data_dir()
    for fname in os.listdir(base_dir):
        if fname.startswith('config_location_') and fname.endswith('.json'):
            loc_path = os.path.join(base_dir, fname)
            try:
                loc_data = _read_json_file(loc_path)
                if not loc_data:
                    continue
                # 用最新的区域字段覆盖区域文件中的对应字段
                for key in LOCAL_KEYS:
                    if key in local_data:
                        loc_data[key] = local_data[key]
                with open(loc_path, 'w', encoding='utf-8') as f:
                    json.dump(loc_data, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"⚠️ 同步区域配置到 {fname} 失败: {e}")



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
    """
    更新系统配置（分层权限）：
    - 全局字段（域控IP、绑定账号等）：仅 admin 账号可修改
    - 区域独立字段（岗位、OU映射等）：admin 角色用户均可修改（写入各自区域文件）
    """
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，仅管理员可修改系统配置"
        )
    
    # 检测本次请求是否包含全局字段的修改
    has_global_changes = any([
        settings.domain_controller_ip is not None,
        settings.domain_name is not None,
        settings.bind_username is not None,
        settings.bind_password is not None,
        settings.allow_registration is not None,
        settings.audit_log is not None,
        settings.region_options is not None,
    ])
    
    # 全局字段修改：仅限 admin 账号
    if has_global_changes and not is_super_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="域控连接参数、标签打印模板等全局配置仅限 admin 管理员账号修改，如需变更请联系总管理员"
        )
    
    # ========== 处理全局字段（写入 config.json + 同步广播）==========
    if has_global_changes:
        global_data = _read_json_file(get_config_path(None)) or _default_config()
        
        if settings.domain_controller_ip is not None:
            global_data["DOMAIN_CONTROLLER_IP"] = settings.domain_controller_ip
        if settings.domain_name is not None:
            global_data["DOMAIN_NAME"] = settings.domain_name
        if settings.bind_username is not None:
            global_data["BIND_USERNAME"] = settings.bind_username
        if settings.bind_password is not None:
            global_data["BIND_PASSWORD"] = settings.bind_password
        if settings.allow_registration is not None:
            global_data["ALLOW_REGISTRATION"] = settings.allow_registration
        if settings.audit_log is not None:
            global_data["AUDIT_LOG"] = settings.audit_log
        if settings.region_options is not None:
            global_data["REGION_OPTIONS"] = settings.region_options
        if settings.print_template is not None:
            global_data["PRINT_TEMPLATE"] = settings.print_template
        
        # 保存全局配置并同步广播到所有区域文件
        save_config(global_data, None)
        sync_global_to_all_locations(global_data)
    
    # ========== 处理区域独立字段（写入对应区域文件）==========
    has_local_changes = any([
        settings.positions is not None,
        settings.active_region_code is not None,
        settings.ou_group_mapping is not None,
        settings.ou_prefix_mapping is not None,
        settings.default_user_password is not None,
        settings.print_template is not None,
    ])
    
    if has_local_changes:
        # 确定写入目标：admin 超管写入全局文件，区域管理员写入自己的区域文件
        target_location_id = None if is_super_admin(current_user) else current_user.location_id
        target_path = get_config_path(target_location_id)
        target_data = _read_json_file(target_path) or _default_config()
        
        if settings.positions is not None:
            target_data["POSITIONS"] = settings.positions
        if settings.active_region_code is not None:
            target_data["ACTIVE_REGION_CODE"] = settings.active_region_code
        if settings.ou_group_mapping is not None:
            target_data["OU_GROUP_MAPPING"] = settings.ou_group_mapping
        if settings.ou_prefix_mapping is not None:
            target_data["OU_PREFIX_MAPPING"] = settings.ou_prefix_mapping
        if settings.default_user_password is not None:
            target_data["DEFAULT_USER_PASSWORD"] = settings.default_user_password
        if settings.print_template is not None:
            target_data["PRINT_TEMPLATE"] = settings.print_template
        
        save_config(target_data, target_location_id)
        if is_super_admin(current_user):
            sync_local_to_all_locations(target_data)
    
    # 审计日志
    action_desc = '全局系统配置（已同步至所有区域）' if has_global_changes else '区域参数配置'
    log_action(db, (current_user.display_name or current_user.username), 'settings', 'UPDATE_SETTINGS', action_desc, device_source=device)
    
    # 返回合并后的最新配置
    merged_config = load_config(current_user.location_id)
    return {"success": True, "message": "配置更新成功", "data": merged_config}

@router.get("/export")
def export_settings(current_user: Any = Depends(get_current_active_user)):
    """导出系统配置文件与数据库包"""
    if not is_super_admin(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限导出，仅限 admin 账号")
    
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
    if not is_super_admin(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限导入，仅限 admin 账号")
    
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
    if not is_super_admin(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权进行AD测试，仅限 admin 账号")
    
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

