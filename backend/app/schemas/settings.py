from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


class BusinessHoursItem(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6)
    open_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    close_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    is_closed: bool = False


class BusinessHoursResponse(BusinessHoursItem):
    id: str
    organization_id: str

    class Config:
        from_attributes = True


class HolidayCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    date: date
    is_recurring: bool = False


class HolidayResponse(HolidayCreate):
    id: str
    organization_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class BusinessSettingsUpdate(BaseModel):
    business_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    industry: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=50)
    human_transfer_phone: Optional[str] = Field(None, max_length=50)
    default_appointment_duration: Optional[int] = Field(None, ge=5, le=480)
    buffer_time_minutes: Optional[int] = Field(None, ge=0, le=120)
    max_booking_days_in_advance: Optional[int] = Field(None, ge=1, le=365)
    min_booking_notice_hours: Optional[int] = Field(None, ge=0, le=72)
    cancellation_notice_hours: Optional[int] = Field(None, ge=0, le=72)
    cancellation_policy: Optional[str] = None
    ai_greeting_en: Optional[str] = None
    ai_greeting_hi: Optional[str] = None
    supported_languages: Optional[str] = Field(None, max_length=50)
    prompt_instructions: Optional[str] = None
    vapi_assistant_id: Optional[str] = None


class BusinessSettingsResponse(BaseModel):
    id: str
    organization_id: str
    business_name: str
    description: Optional[str] = None
    industry: str
    address: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    human_transfer_phone: Optional[str] = None
    default_appointment_duration: int
    buffer_time_minutes: int
    max_booking_days_in_advance: int
    min_booking_notice_hours: int
    cancellation_notice_hours: int
    cancellation_policy: Optional[str] = None
    ai_greeting_en: Optional[str] = None
    ai_greeting_hi: Optional[str] = None
    supported_languages: str
    prompt_instructions: Optional[str] = None
    vapi_assistant_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
