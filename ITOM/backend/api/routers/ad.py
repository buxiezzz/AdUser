from fastapi import APIRouter, Depends, HTTPException
from typing import List

from schemas.ad import ADUserCreate, ADUserResponse, OUListResponse, GroupListResponse
from core.ad_utils import create_ad_user, get_ou_list, get_group_list, get_base_dn
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
