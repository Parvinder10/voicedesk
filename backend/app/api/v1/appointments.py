from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_org
from app.models import Appointment, Organization
from app.schemas.appointment import (
    AppointmentCreate, AppointmentReschedule, AppointmentCancel,
    AppointmentUpdate, AppointmentResponse
)
from app.services.appointment_service import AppointmentService

router = APIRouter(prefix="/appointments", tags=["Appointments"])


@router.get("", response_model=List[AppointmentResponse])
def list_appointments(
    status: Optional[str] = Query(None, description="Filter by status (Confirmed, Cancelled, Completed, etc.)"),
    customer_id: Optional[str] = Query(None),
    staff_id: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """List appointments for the organization with rich filtering options."""
    query = db.query(Appointment).filter(Appointment.organization_id == org.id)
    if status:
        query = query.filter(Appointment.status == status)
    if customer_id:
        query = query.filter(Appointment.customer_id == customer_id)
    if staff_id:
        query = query.filter(Appointment.staff_id == staff_id)
    if start_date:
        query = query.filter(Appointment.start_time >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(Appointment.end_time <= datetime.combine(end_date, datetime.max.time()))

    appts = query.order_by(Appointment.start_time.asc()).offset(skip).limit(limit).all()
    return [AppointmentService._format_appointment_response(a) for a in appts]


@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def book_appointment(
    data: AppointmentCreate,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """
    Book a genuine appointment.
    Applies concurrency-safe double-booking prevention and validates staff availability.
    """
    return AppointmentService.book_appointment(db=db, org=org, data=data)


@router.get("/{id}", response_model=AppointmentResponse)
def get_appointment(
    id: str,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """Retrieve appointment details."""
    appt = db.query(Appointment).filter(
        Appointment.id == id,
        Appointment.organization_id == org.id
    ).first()
    if not appt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found.")
    return AppointmentService._format_appointment_response(appt)


@router.patch("/{id}", response_model=AppointmentResponse)
def update_appointment(
    id: str,
    update_data: AppointmentUpdate,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """Update appointment status, staff, or notes."""
    appt = db.query(Appointment).filter(
        Appointment.id == id,
        Appointment.organization_id == org.id
    ).first()
    if not appt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found.")

    patch = update_data.model_dump(exclude_unset=True)
    for field, val in patch.items():
        setattr(appt, field, val)

    db.commit()
    db.refresh(appt)
    return AppointmentService._format_appointment_response(appt)


@router.post("/{id}/reschedule", response_model=AppointmentResponse)
def reschedule_appointment(
    id: str,
    data: AppointmentReschedule,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """Reschedule an existing appointment to a new available time slot."""
    return AppointmentService.reschedule_appointment(
        db=db,
        org=org,
        appointment_id=id,
        data=data
    )


@router.post("/{id}/cancel", response_model=AppointmentResponse)
def cancel_appointment(
    id: str,
    data: AppointmentCancel,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """Cancel an appointment and record cancellation reason."""
    return AppointmentService.cancel_appointment(
        db=db,
        org=org,
        appointment_id=id,
        data=data
    )
