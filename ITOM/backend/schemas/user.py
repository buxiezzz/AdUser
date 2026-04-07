from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    role: Optional[str] = "user"

class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    role: str
    is_active: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
