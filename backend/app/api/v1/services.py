from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_org
from app.models import Service, Organization
from app.schemas.service import ServiceCreate, ServiceUpdate, ServiceResponse

router = APIRouter(prefix="/services", tags=["Services"])


@router.get("", response_model=List[ServiceResponse])
def list_services(
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """Retrieve all services offered by the authenticated organization."""
    return db.query(Service).filter(
        Service.organization_id == org.id,
        Service.is_active == True
    ).order_by(Service.name.asc()).all()


@router.post("", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
def create_service(
    service_in: ServiceCreate,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """Create a new service with pricing and appointment duration."""
    service = Service(
        organization_id=org.id,
        name=service_in.name,
        description=service_in.description,
        duration_minutes=service_in.duration_minutes,
        price=service_in.price,
        currency=service_in.currency,
        is_active=service_in.is_active
    )
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


@router.patch("/{id}", response_model=ServiceResponse)
def update_service(
    id: str,
    service_update: ServiceUpdate,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """Update service attributes."""
    service = db.query(Service).filter(
        Service.id == id,
        Service.organization_id == org.id
    ).first()
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found.")

    update_data = service_update.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(service, field, val)

    db.commit()
    db.refresh(service)
    return service


@router.delete("/{id}", status_code=status.HTTP_200_OK)
def delete_service(
    id: str,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """Deactivate or remove a service."""
    service = db.query(Service).filter(
        Service.id == id,
        Service.organization_id == org.id
    ).first()
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found.")

    # Soft delete to preserve historical appointments
    service.is_active = False
    db.commit()
    return {"message": "Service deactivated successfully.", "id": id}
