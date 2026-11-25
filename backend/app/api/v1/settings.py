from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_org
from app.models import BusinessSettings, BusinessHours, Holiday, Organization
from app.schemas.settings import (
    BusinessSettingsUpdate, BusinessSettingsResponse,
    BusinessHoursItem, BusinessHoursResponse,
    HolidayCreate, HolidayResponse
)

router = APIRouter(prefix="/settings", tags=["Business Settings"])


@router.get("", response_model=BusinessSettingsResponse)
def get_settings(
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """Retrieve business settings and voice agent configuration for the organization."""
    settings = db.query(BusinessSettings).filter_by(organization_id=org.id).first()
    if not settings:
        # Create default if missing
        settings = BusinessSettings(
            organization_id=org.id,
            business_name=org.name,
            industry="clinic"
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


@router.patch("", response_model=BusinessSettingsResponse)
def update_settings(
    settings_update: BusinessSettingsUpdate,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """Update business settings and agent configuration."""
    settings = db.query(BusinessSettings).filter_by(organization_id=org.id).first()
    if not settings:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Settings not found.")

    update_data = settings_update.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(settings, field, val)

    # Sync organization name if business_name was updated
    if "business_name" in update_data and update_data["business_name"]:
        org.name = update_data["business_name"]
        db.add(org)

    db.commit()
    db.refresh(settings)
    return settings


@router.get("/hours", response_model=List[BusinessHoursResponse])
def get_business_hours(
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """Retrieve operating hours for each day of the week."""
    hours = db.query(BusinessHours).filter_by(organization_id=org.id).order_by(BusinessHours.day_of_week.asc()).all()
    return hours


@router.put("/hours", response_model=List[BusinessHoursResponse])
def update_business_hours(
    hours_list: List[BusinessHoursItem],
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """Update operating hours schedule for the organization."""
    for item in hours_list:
        bh = db.query(BusinessHours).filter_by(
            organization_id=org.id,
            day_of_week=item.day_of_week
        ).first()
        if bh:
            bh.open_time = item.open_time
            bh.close_time = item.close_time
            bh.is_closed = item.is_closed
        else:
            bh = BusinessHours(
                organization_id=org.id,
                day_of_week=item.day_of_week,
                open_time=item.open_time,
                close_time=item.close_time,
                is_closed=item.is_closed
            )
            db.add(bh)

    db.commit()
    return db.query(BusinessHours).filter_by(organization_id=org.id).order_by(BusinessHours.day_of_week.asc()).all()


@router.get("/holidays", response_model=List[HolidayResponse])
def list_holidays(
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """Retrieve all upcoming scheduled holidays and closures."""
    return db.query(Holiday).filter_by(organization_id=org.id).order_by(Holiday.date.asc()).all()


@router.post("/holidays", response_model=HolidayResponse, status_code=status.HTTP_201_CREATED)
def add_holiday(
    holiday_in: HolidayCreate,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """Add a holiday or business closure date."""
    existing = db.query(Holiday).filter_by(
        organization_id=org.id,
        date=holiday_in.date
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A holiday on {holiday_in.date} already exists."
        )

    holiday = Holiday(
        organization_id=org.id,
        name=holiday_in.name,
        date=holiday_in.date,
        is_recurring=holiday_in.is_recurring
    )
    db.add(holiday)
    db.commit()
    db.refresh(holiday)
    return holiday


@router.delete("/holidays/{id}", status_code=status.HTTP_200_OK)
def delete_holiday(
    id: str,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """Delete a scheduled holiday."""
    holiday = db.query(Holiday).filter_by(
        id=id,
        organization_id=org.id
    ).first()
    if not holiday:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holiday not found.")

    db.delete(holiday)
    db.commit()
    return {"message": "Holiday removed successfully.", "id": id}
