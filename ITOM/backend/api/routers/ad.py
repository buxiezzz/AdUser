from fastapi import APIRouter, Depends, HTTPException
from typing import List

from schemas.ad import ADUserCreate, ADUserResponse, OUListResponse, GroupListResponse, UserPasswordUpdate, UserOUUpdate, UserGroupsUpdate, GroupMembersUpdate
from core.ad_utils import create_ad_user, get_ou_list, get_group_list, get_base_dn, search_ad_users, get_ad_user_detail, change_user_password, move_user_ou, update_user_groups, get_group_members, update_group_members
from core.utils import simplify_dn
from api.deps import get_current_active_user
from models.user import User
from api.routers.settings import load_config

router = APIRouter()

@router.post("/users", response_model=ADUserResponse)
def api_create_ad_user(payload: ADUserCreate, current_user: User = Depends(get_current_active_user)):
    config = load_config()
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
        groups_to_add=payload.groups
    )
    if not success:
        # 这里对于失败我们返回 400 Bad Request
        raise HTTPException(status_code=400, detail=message)
    return {"success": True, "message": message}

@router.get("/users")
def api_search_ad_users(keyword: str = "", current_user: User = Depends(get_current_active_user)):
    config = load_config()
    sys_bind_user = config.get('BIND_USERNAME', '')
    sys_bind_pass = config.get('BIND_PASSWORD', '')
    
    users = search_ad_users(sys_bind_user, sys_bind_pass, keyword)
    return {"users": users}

@router.get("/users/{username}")
def api_get_ad_user_detail(username: str, current_user: User = Depends(get_current_active_user)):
    config = load_config()
    sys_bind_user = config.get('BIND_USERNAME', '')
    sys_bind_pass = config.get('BIND_PASSWORD', '')
    
    detail = get_ad_user_detail(sys_bind_user, sys_bind_pass, username)
    if not detail:
        raise HTTPException(status_code=404, detail="未找到该用户")
    return {"user": detail}

@router.put("/users/{username}/password")
def api_update_user_password(username: str, payload: UserPasswordUpdate, current_user: User = Depends(get_current_active_user)):
    config = load_config()
    sys_bind_user = config.get('BIND_USERNAME', '')
    sys_bind_pass = config.get('BIND_PASSWORD', '')
    
    success, msg = change_user_password(sys_bind_user, sys_bind_pass, payload.user_dn, payload.new_password)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "message": msg}

@router.put("/users/{username}/ou")
def api_update_user_ou(username: str, payload: UserOUUpdate, current_user: User = Depends(get_current_active_user)):
    config = load_config()
    sys_bind_user = config.get('BIND_USERNAME', '')
    sys_bind_pass = config.get('BIND_PASSWORD', '')
    
    success, msg = move_user_ou(sys_bind_user, sys_bind_pass, payload.user_dn, payload.new_ou_dn)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "message": msg}

@router.put("/users/{username}/groups")
def api_update_user_groups(username: str, payload: UserGroupsUpdate, current_user: User = Depends(get_current_active_user)):
    config = load_config()
    sys_bind_user = config.get('BIND_USERNAME', '')
    sys_bind_pass = config.get('BIND_PASSWORD', '')
    
    success, msg = update_user_groups(sys_bind_user, sys_bind_pass, payload.user_dn, payload.old_groups, payload.new_groups)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "message": msg}


@router.get("/ous", response_model=List[OUListResponse])
def api_get_ou_list(current_user: User = Depends(get_current_active_user)):
    config = load_config()
    sys_domain_name = config.get('DOMAIN_NAME', '')
    sys_bind_user = config.get('BIND_USERNAME', '')
    sys_bind_pass = config.get('BIND_PASSWORD', '')

    ou_options_raw = get_ou_list(sys_bind_user, sys_bind_pass)
    base_dn = get_base_dn(sys_domain_name)
    return [{'dn': dn, 'name': simplify_dn(dn, base_dn)} for dn in ou_options_raw]

@router.get("/groups", response_model=GroupListResponse)
def api_get_group_list(current_user: User = Depends(get_current_active_user)):
    config = load_config()
    sys_bind_user = config.get('BIND_USERNAME', '')
    sys_bind_pass = config.get('BIND_PASSWORD', '')

    groups = get_group_list(sys_bind_user, sys_bind_pass)
    return {"groups": groups}

from pydantic import BaseModel
class GetGroupMembersRequest(BaseModel):
    group_dn: str

@router.post("/group-members/list")
def api_get_group_members(payload: GetGroupMembersRequest, current_user: User = Depends(get_current_active_user)):
    config = load_config()
    sys_bind_user = config.get('BIND_USERNAME', '')
    sys_bind_pass = config.get('BIND_PASSWORD', '')
    
    members = get_group_members(sys_bind_user, sys_bind_pass, payload.group_dn)
    return {"members": members}

@router.put("/group-members/update")
def api_update_group_members(payload: GroupMembersUpdate, current_user: User = Depends(get_current_active_user)):
    config = load_config()
    sys_bind_user = config.get('BIND_USERNAME', '')
    sys_bind_pass = config.get('BIND_PASSWORD', '')
    
    success, msg = update_group_members(sys_bind_user, sys_bind_pass, payload.group_dn, payload.old_members, payload.new_members)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "message": msg}
