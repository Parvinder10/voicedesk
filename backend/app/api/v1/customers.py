import re
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import get_db
from app.core.deps import get_current_org
from app.models import Customer, Organization, Appointment, Call
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse, CustomerDetailResponse

router = APIRouter(prefix="/customers", tags=["Customers"])


def normalize_phone(phone: str) -> str:
    cleaned = re.sub(r'[\s\(\)\-\.]', '', phone)
    if not cleaned.startswith("+") and len(cleaned) == 10:
        cleaned = "+91" + cleaned  # default country code if missing
    return cleaned


@router.get("", response_model=List[CustomerResponse])
def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    q: Optional[str] = Query(None, description="Search by name or phone"),
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """Retrieve customers for the authenticated organization with optional search and pagination."""
    query = db.query(Customer).filter(Customer.organization_id == org.id)
    if q:
        search_filter = f"%{q}%"
        query = query.filter(
            or_(
                Customer.name.ilike(search_filter),
                Customer.phone.ilike(search_filter),
                Customer.email.ilike(search_filter)
            )
        )
    return query.order_by(Customer.created_at.desc()).offset(skip).limit(limit).all()


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(
    customer_in: CustomerCreate,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """Create a new customer profile. Rejects duplicate phone numbers for the same organization."""
    phone = normalize_phone(customer_in.phone)
    existing = db.query(Customer).filter(
        Customer.organization_id == org.id,
        Customer.phone == phone
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Customer with phone number {phone} already exists in your organization."
        )

    customer = Customer(
        organization_id=org.id,
        phone=phone,
        name=customer_in.name,
        email=customer_in.email,
        notes=customer_in.notes,
        metadata_json=customer_in.metadata_json or "{}"
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/{id}", response_model=CustomerDetailResponse)
def get_customer(
    id: str,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """Get complete customer profile including past appointment history and call logs."""
    customer = db.query(Customer).filter(
        Customer.id == id,
        Customer.organization_id == org.id
    ).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found.")

    # Recent appointments
    appointments = db.query(Appointment).filter(
        Appointment.customer_id == customer.id,
        Appointment.organization_id == org.id
    ).order_by(Appointment.start_time.desc()).limit(10).all()

    # Recent calls
    calls = db.query(Call).filter(
        Call.customer_id == customer.id,
        Call.organization_id == org.id
    ).order_by(Call.created_at.desc()).limit(10).all()

    appointments_list = [
        {
            "id": a.id,
            "service_name": a.service.name if a.service else "Service",
            "start_time": a.start_time.isoformat() if a.start_time else None,
            "end_time": a.end_time.isoformat() if a.end_time else None,
            "status": a.status,
            "staff_name": a.staff.name if a.staff else None
        }
        for a in appointments
    ]

    calls_list = [
        {
            "id": c.id,
            "caller_phone": c.caller_phone,
            "status": c.status,
            "duration_seconds": c.duration_seconds,
            "outcome": c.outcome,
            "created_at": c.created_at.isoformat() if c.created_at else None
        }
        for c in calls
    ]

    return CustomerDetailResponse(
        id=customer.id,
        organization_id=customer.organization_id,
        phone=customer.phone,
        name=customer.name,
        email=customer.email,
        notes=customer.notes,
        metadata_json=customer.metadata_json,
        created_at=customer.created_at,
        updated_at=customer.updated_at,
        appointments_count=len(appointments),
        calls_count=len(calls),
        recent_appointments=appointments_list,
        recent_calls=calls_list
    )


@router.patch("/{id}", response_model=CustomerResponse)
def update_customer(
    id: str,
    customer_update: CustomerUpdate,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """Update customer details."""
    customer = db.query(Customer).filter(
        Customer.id == id,
        Customer.organization_id == org.id
    ).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found.")

    update_data = customer_update.model_dump(exclude_unset=True)
    if "phone" in update_data and update_data["phone"]:
        new_phone = normalize_phone(update_data["phone"])
        # Check duplicate
        existing = db.query(Customer).filter(
            Customer.organization_id == org.id,
            Customer.phone == new_phone,
            Customer.id != customer.id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Another customer already has phone {new_phone}."
            )
        customer.phone = new_phone

    for field in ["name", "email", "notes", "metadata_json"]:
        if field in update_data:
            setattr(customer, field, update_data[field])

    db.commit()
    db.refresh(customer)
    return customer
