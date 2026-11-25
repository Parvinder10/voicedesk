from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    business_name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    industry: Optional[str] = Field("clinic", max_length=100)
    timezone: Optional[str] = Field("Asia/Kolkata", max_length=50)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenRefresh(BaseModel):
    refresh_token: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class OrganizationResponse(BaseModel):
    id: str
    name: str
    slug: str
    phone: Optional[str] = None
    timezone: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: str
    organization_id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    user: UserResponse
    organization: OrganizationResponse
    token: Token


class CurrentUserWithOrg(BaseModel):
    user: UserResponse
    organization: OrganizationResponse
