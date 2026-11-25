from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_org
from app.models import Staff, Organization
from app.schemas.staff import StaffCreate, StaffUpdate, StaffResponse

router = APIRouter(prefix="/staff", tags=["Staff"])


@router.get("", response_model=List[StaffResponse])
def list_staff(
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """Retrieve all staff members of the authenticated organization."""
    return db.query(Staff).filter(
        Staff.organization_id == org.id,
        Staff.is_active == True
    ).order_by(Staff.name.asc()).all()


@router.post("", response_model=StaffResponse, status_code=status.HTTP_201_CREATED)
def create_staff(
    staff_in: StaffCreate,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """Create a new staff member profile."""
    staff = Staff(
        organization_id=org.id,
        name=staff_in.name,
        email=staff_in.email,
        phone=staff_in.phone,
        title=staff_in.title,
        is_active=staff_in.is_active
    )
    db.add(staff)
    db.commit()
    db.refresh(staff)
    return staff


@router.patch("/{id}", response_model=StaffResponse)
def update_staff(
    id: str,
    staff_update: StaffUpdate,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """Update staff details."""
    staff = db.query(Staff).filter(
        Staff.id == id,
        Staff.organization_id == org.id
    ).first()
    if not staff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff member not found.")

    update_data = staff_update.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(staff, field, val)

    db.commit()
    db.refresh(staff)
    return staff


@router.delete("/{id}", status_code=status.HTTP_200_OK)
def delete_staff(
    id: str,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """Deactivate a staff member."""
    staff = db.query(Staff).filter(
        Staff.id == id,
        Staff.organization_id == org.id
    ).first()
    if not staff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff member not found.")

    staff.is_active = False
    db.commit()
    return {"message": "Staff member deactivated successfully.", "id": id}
