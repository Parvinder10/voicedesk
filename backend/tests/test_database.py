import pytest
from app.database import Base, engine, SessionLocal
from app.models import Organization, BusinessSettings, BusinessHours


def test_database_initialization():
    db = SessionLocal()
    try:
        # Create an organization
        org = Organization(
            name="Apex Health Clinic",
            slug="apex-health-clinic",
            phone="+919876543210",
            timezone="Asia/Kolkata"
        )
        db.add(org)
        db.commit()
        db.refresh(org)

        assert org.id is not None
        assert org.name == "Apex Health Clinic"

        # Add business settings
        settings = BusinessSettings(
            organization_id=org.id,
            business_name=org.name,
            industry="clinic",
            contact_phone=org.phone
        )
        db.add(settings)

        # Add business hours (Monday)
        bh = BusinessHours(
            organization_id=org.id,
            day_of_week=0,
            open_time="09:00",
            close_time="17:00",
            is_closed=False
        )
        db.add(bh)
        db.commit()

        # Query back
        fetched_org = db.query(Organization).filter_by(slug="apex-health-clinic").first()
        assert fetched_org is not None
        assert fetched_org.settings.business_name == "Apex Health Clinic"
        assert len(fetched_org.business_hours) == 1
        assert fetched_org.business_hours[0].open_time == "09:00"

        # Cleanup
        db.delete(fetched_org)
        db.commit()
    finally:
        db.close()
