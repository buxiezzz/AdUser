from pydantic import BaseModel
from typing import Optional, List

# AD User Creation Request Payload
class ADUserCreate(BaseModel):
    new_username: str
    new_display_name: str
    ou_path: str
    password: str
    position_name: Optional[str] = None
    groups: Optional[List[str]] = []
    
    # 因为后端分离我们不再能依赖 Flask Session 传递下面这些高权限凭证了，
    # 在实际生产中，要么由系统统一存储一个超级域管账号(通过配置)，
    # 要么让前端发请求时传递 admin 自身的 AD 凭据。 这里我们采用配置统一存储的方式。
    # bind_username: str
    # bind_password: str

class ADUserResponse(BaseModel):
    success: bool
    message: str

class OUListResponse(BaseModel):
    dn: str
    name: str

class GroupListResponse(BaseModel):
    groups: List[str]
