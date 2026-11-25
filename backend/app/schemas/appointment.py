from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class AppointmentCreate(BaseModel):
    service_id: str
    customer_id: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    staff_id: Optional[str] = None
    start_time: datetime
    notes: Optional[str] = None
    call_id: Optional[str] = None


class AppointmentReschedule(BaseModel):
    new_start_time: datetime
    staff_id: Optional[str] = None
    reason: Optional[str] = None


class AppointmentCancel(BaseModel):
    reason: Optional[str] = Field("Customer requested cancellation", min_length=2)


class AppointmentUpdate(BaseModel):
    staff_id: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = Field(None, pattern=r"^(Pending|Confirmed|Rescheduled|Cancelled|Completed|No-show)$")


class AppointmentResponse(BaseModel):
    id: str
    organization_id: str
    customer_id: str
    service_id: str
    staff_id: Optional[str] = None
    call_id: Optional[str] = None
    start_time: datetime
    end_time: datetime
    status: str
    notes: Optional[str] = None
    cancellation_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Nested fields for UI display
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    service_name: Optional[str] = None
    service_price: Optional[float] = None
    staff_name: Optional[str] = None

    class Config:
        from_attributes = True
