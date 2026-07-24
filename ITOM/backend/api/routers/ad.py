from fastapi import APIRouter, Depends, HTTPException
from typing import List
from schemas.ad import ADUserCreate, ADUserResponse, OUListResponse, GroupListResponse, UserPasswordUpdate, UserOUUpdate, UserGroupsUpdate, GroupMembersUpdate, UserStatusUpdate, BatchDisableUsersRequest
from core.ad_utils import create_ad_user, get_ou_list, get_group_list, get_base_dn, search_ad_users, get_ad_user_detail, change_user_password, move_user_ou, update_user_groups, get_group_members, update_group_members, toggle_ad_user_status, batch_disable_ad_users
from core.utils import simplify_dn
from api.deps import get_current_active_user, get_device_source
from database import get_db
from sqlalchemy.orm import Session
from crud.audit import log_action
from models.user import User
from api.routers.settings import load_config
import io
from openpyxl import Workbook
from fastapi.responses import StreamingResponse
from datetime import datetime

router = APIRouter()

@router.put("/users/{username}/status")
def api_update_user_status(username: str, payload: UserStatusUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user), device: str = Depends(get_device_source)):
    config = load_config(current_user.location_id)
    sys_bind_user = config.get('BIND_USERNAME', '')
    sys_bind_pass = config.get('BIND_PASSWORD', '')
    
    success, msg = toggle_ad_user_status(sys_bind_user, sys_bind_pass, payload.user_dn, payload.enabled, location_id=current_user.location_id)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    
    log_action(db, (current_user.display_name or current_user.username), 'ad', 'STATUS_UPDATE', username, {'dn': payload.user_dn, 'enabled': payload.enabled}, device_source=device)
    return {"success": True, "message": msg}

@router.post("/users", response_model=ADUserResponse)
def api_create_ad_user(payload: ADUserCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user), device: str = Depends(get_device_source)):
    config = load_config(current_user.location_id)
    sys_domain_name = config.get('DOMAIN_NAME', '')
    sys_dc_ip = config.get('DOMAIN_CONTROLLER_IP', '')
    sys_bind_user = config.get('BIND_USERNAME', '')
    sys_bind_pass = config.get('BIND_PASSWORD', '')
    
    success, message = create_ad_user(
        domain_controller_ip=sys_dc_ip,
        bind_username=sys_bind_user,
        bind_password=sys_bind_pass,
        username=payload.new_username,
        display_name=payload.new_display_name,
        password=payload.password,
        ou_path=payload.ou_path,
        domain_name=sys_domain_name,
        position_name=payload.position_name,
        groups_to_add=payload.groups, location_id=current_user.location_id
    )
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    log_action(db, (current_user.display_name or current_user.username), 'ad', 'PROVISION', payload.new_username, 
               {'display_name': payload.new_display_name, 'ou': payload.ou_path, 'position': payload.position_name}, device_source=device)
    return {"success": True, "message": message}

@router.get("/users")
def api_search_ad_users(keyword: str = "", current_user: User = Depends(get_current_active_user)):
    config = load_config(current_user.location_id)
    sys_bind_user = config.get('BIND_USERNAME', '')
    sys_bind_pass = config.get('BIND_PASSWORD', '')
    
    users = search_ad_users(sys_bind_user, sys_bind_pass, keyword, location_id=current_user.location_id)
    return {"users": users}

@router.get("/users/export")
def api_export_ad_users(keyword: str = "", db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user), device: str = Depends(get_device_source)):
    config = load_config(current_user.location_id)
    sys_bind_user = config.get('BIND_USERNAME', '')
    sys_bind_pass = config.get('BIND_PASSWORD', '')
    sys_domain_name = config.get('DOMAIN_NAME', '')
    base_dn = get_base_dn(sys_domain_name)
    
    users = search_ad_users(sys_bind_user, sys_bind_pass, keyword, location_id=current_user.location_id)
    
    # 创建 Excel 工作簿
    wb = Workbook()
    ws = wb.active
    ws.title = "域用户列表"
    
    # 写入表头
    headers = ["姓名", "用户工号", "邮箱", "所属组织", "状态", "更新时间"]
    ws.append(headers)
    
    # 填充数据
    for u in users:
        status_text = "正常" if u.get('enabled') else "已禁用"
        
        ws.append([
            u.get('display_name', ''),
            u.get('username', ''),
            u.get('email', ''),
            simplify_dn(u.get('dn', ''), base_dn),
            status_text,
            u.get('updated_at', '')
        ])
    
    # 保存到流
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    log_action(db, (current_user.display_name or current_user.username), 'ad', 'EXPORT_USERS', f"关键词: {keyword}", device_source=device)
    
    filename = f"Domain_Users_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/users/{username}")
def api_get_ad_user_detail(username: str, current_user: User = Depends(get_current_active_user)):
    config = load_config(current_user.location_id)
    sys_bind_user = config.get('BIND_USERNAME', '')
    sys_bind_pass = config.get('BIND_PASSWORD', '')
    
    detail = get_ad_user_detail(sys_bind_user, sys_bind_pass, username, location_id=current_user.location_id)
    if not detail:
        raise HTTPException(status_code=404, detail="未找到该用户")
    return {"user": detail}

@router.put("/users/{username}/password")
def api_update_user_password(username: str, payload: UserPasswordUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user), device: str = Depends(get_device_source)):
    config = load_config(current_user.location_id)
    sys_bind_user = config.get('BIND_USERNAME', '')
    sys_bind_pass = config.get('BIND_PASSWORD', '')
    
    success, msg = change_user_password(sys_bind_user, sys_bind_pass, payload.user_dn, payload.new_password, location_id=current_user.location_id)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    
    log_action(db, (current_user.display_name or current_user.username), 'ad', 'PASSWORD_RESET', username, {'dn': payload.user_dn}, device_source=device)
    return {"success": True, "message": msg}

@router.put("/users/{username}/ou")
def api_update_user_ou(username: str, payload: UserOUUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user), device: str = Depends(get_device_source)):
    config = load_config(current_user.location_id)
    sys_bind_user = config.get('BIND_USERNAME', '')
    sys_bind_pass = config.get('BIND_PASSWORD', '')
    
    success, msg = move_user_ou(sys_bind_user, sys_bind_pass, payload.user_dn, payload.new_ou_dn, location_id=current_user.location_id)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    
    log_action(db, (current_user.display_name or current_user.username), 'ad', 'MOVE_OU', username, {'old_dn': payload.user_dn, 'new_dn': payload.new_ou_dn}, device_source=device)
    return {"success": True, "message": msg}

@router.put("/users/{username}/groups")
def api_update_user_groups(username: str, payload: UserGroupsUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user), device: str = Depends(get_device_source)):
    config = load_config(current_user.location_id)
    sys_bind_user = config.get('BIND_USERNAME', '')
    sys_bind_pass = config.get('BIND_PASSWORD', '')
    
    success, msg = update_user_groups(sys_bind_user, sys_bind_pass, payload.user_dn, payload.old_groups, payload.new_groups, location_id=current_user.location_id)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    
    log_action(db, (current_user.display_name or current_user.username), 'ad', 'GROUP_UPDATE', username, {'old': payload.old_groups, 'new': payload.new_groups}, device_source=device)
    return {"success": True, "message": msg}


@router.get("/ous", response_model=List[OUListResponse])
def api_get_ou_list(apply_filter: bool = False, current_user: User = Depends(get_current_active_user)):
    config = load_config(current_user.location_id)
    sys_domain_name = config.get('DOMAIN_NAME', '')
    sys_bind_user = config.get('BIND_USERNAME', '')
    sys_bind_pass = config.get('BIND_PASSWORD', '')

    ou_options_raw = get_ou_list(sys_bind_user, sys_bind_pass, location_id=current_user.location_id, apply_filter=apply_filter)
    base_dn = get_base_dn(sys_domain_name)
    return [{'dn': dn, 'name': simplify_dn(dn, base_dn)} for dn in ou_options_raw]

@router.get("/groups", response_model=GroupListResponse)
def api_get_group_list(current_user: User = Depends(get_current_active_user)):
    config = load_config(current_user.location_id)
    sys_bind_user = config.get('BIND_USERNAME', '')
    sys_bind_pass = config.get('BIND_PASSWORD', '')

    groups = get_group_list(sys_bind_user, sys_bind_pass, location_id=current_user.location_id)
    return {"groups": groups}

from pydantic import BaseModel
class GetGroupMembersRequest(BaseModel):
    group_dn: str

@router.post("/group-members/list")
def api_get_group_members(payload: GetGroupMembersRequest, current_user: User = Depends(get_current_active_user)):
    config = load_config(current_user.location_id)
    sys_bind_user = config.get('BIND_USERNAME', '')
    sys_bind_pass = config.get('BIND_PASSWORD', '')
    
    members = get_group_members(sys_bind_user, sys_bind_pass, payload.group_dn, location_id=current_user.location_id)
    return {"members": members}

@router.put("/group-members/update")
def api_update_group_members(payload: GroupMembersUpdate, current_user: User = Depends(get_current_active_user)):
    config = load_config(current_user.location_id)
    sys_bind_user = config.get('BIND_USERNAME', '')
    sys_bind_pass = config.get('BIND_PASSWORD', '')
    
    success, msg = update_group_members(sys_bind_user, sys_bind_pass, payload.group_dn, payload.old_members, payload.new_members, location_id=current_user.location_id)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "message": msg}

@router.post("/users/batch-disable")
def api_batch_disable_users(payload: BatchDisableUsersRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user), device: str = Depends(get_device_source)):
    config = load_config(current_user.location_id)
    sys_bind_user = config.get('BIND_USERNAME', '')
    sys_bind_pass = config.get('BIND_PASSWORD', '')
    
    user_items = [u.dict() for u in payload.users]
    success, msg, details = batch_disable_ad_users(
        sys_bind_user, sys_bind_pass, user_items, payload.target_ou_dn, location_id=current_user.location_id
    )
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    
    log_action(db, (current_user.display_name or current_user.username), 'ad', 'BATCH_DISABLE_USERS', 
               f"批量禁用 {len(payload.users)} 名员工", 
               {'user_count': len(payload.users), 'target_ou': payload.target_ou_dn}, device_source=device)
    return {"success": True, "message": msg, "details": details}


