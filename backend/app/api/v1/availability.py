from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_org
from app.models import Organization, AvailabilityRule
from app.schemas.availability import (
    AvailabilityResponse, AvailabilityRuleCreate, AvailabilityRuleResponse
)
from app.services.availability_service import AvailabilityService

router = APIRouter(prefix="/availability", tags=["Availability"])


@router.get("", response_model=AvailabilityResponse)
def get_availability(
    service_id: str = Query(..., description="Service ID to check availability for"),
    date: date = Query(..., description="Target date (YYYY-MM-DD)"),
    staff_id: Optional[str] = Query(None, description="Optional staff ID to filter by"),
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """
    Calculate and return available real-time appointment booking slots
    grounded in actual business hours, staff schedules, breaks, and existing appointments.
    """
    return AvailabilityService.get_available_slots(
        db=db,
        org=org,
        service_id=service_id,
        target_date=date,
        staff_id=staff_id
    )


@router.get("/rules", response_model=List[AvailabilityRuleResponse])
def list_availability_rules(
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """List all custom availability rules, breaks, and vacation schedules."""
    return db.query(AvailabilityRule).filter_by(organization_id=org.id).all()


@router.post("/rules", response_model=AvailabilityRuleResponse, status_code=status.HTTP_201_CREATED)
def create_availability_rule(
    rule_in: AvailabilityRuleCreate,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """Create a staff availability rule (e.g. daily lunch break or vacation)."""
    rule = AvailabilityRule(
        organization_id=org.id,
        staff_id=rule_in.staff_id,
        rule_type=rule_in.rule_type,
        start_datetime=rule_in.start_datetime,
        end_datetime=rule_in.end_datetime,
        day_of_week=rule_in.day_of_week,
        start_time=rule_in.start_time,
        end_time=rule_in.end_time,
        reason=rule_in.reason
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule
