from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class AvailabilityQuery(BaseModel):
    service_id: str
    date: date
    staff_id: Optional[str] = None


class TimeSlot(BaseModel):
    start_time: datetime
    end_time: datetime
    formatted_time: str
    available_staff_id: Optional[str] = None
    available_staff_name: Optional[str] = None


class AvailabilityResponse(BaseModel):
    date: date
    service_id: str
    service_name: str
    duration_minutes: int
    timezone: str
    is_available: bool
    reason: Optional[str] = None
    available_slots: List[TimeSlot]


class AvailabilityRuleCreate(BaseModel):
    staff_id: Optional[str] = None
    rule_type: str = Field(..., pattern=r"^(break|vacation|buffer|custom_hours)$")
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    day_of_week: Optional[int] = Field(None, ge=0, le=6)
    start_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    end_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    reason: Optional[str] = None


class AvailabilityRuleResponse(AvailabilityRuleCreate):
    id: str
    organization_id: str
    created_at: datetime

    class Config:
        from_attributes = True
