from datetime import datetime

from pydantic import BaseModel, EmailStr


class RegisterIn(BaseModel):
    email: EmailStr
    password: str


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class GoogleAuthIn(BaseModel):
    id_token: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str


class UserOut(BaseModel):
    id: str
    email: EmailStr
    created_at: datetime
    rating_count: int = 0
    is_admin: bool = False
    auth_provider: str = "email"


class AdminUserOut(BaseModel):
    id: str
    email: str
    auth_provider: str
    is_admin: bool
    last_login_at: datetime | None
    created_at: datetime
    rating_count: int = 0
