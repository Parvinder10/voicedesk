from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field


class CustomerBase(BaseModel):
    phone: str = Field(..., min_length=5, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    notes: Optional[str] = None
    metadata_json: Optional[str] = "{}"


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone: Optional[str] = Field(None, min_length=5, max_length=50)
    email: Optional[EmailStr] = None
    notes: Optional[str] = None
    metadata_json: Optional[str] = None


class CustomerResponse(CustomerBase):
    id: str
    organization_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CustomerDetailResponse(CustomerResponse):
    appointments_count: int = 0
    calls_count: int = 0
    recent_appointments: List[Dict[str, Any]] = []
    recent_calls: List[Dict[str, Any]] = []
