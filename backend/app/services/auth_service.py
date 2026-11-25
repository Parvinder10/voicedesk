import re
from typing import Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models import (
    Organization, User, BusinessSettings, BusinessHours, Service, Staff, AuditLog
)
from app.core.security import (
    get_password_hash, verify_password, create_access_token, create_refresh_token, decode_token
)
from app.schemas.auth import UserRegister, UserLogin, Token


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text.strip('-')


class AuthService:
    @staticmethod
    def register_business(db: Session, reg_data: UserRegister) -> Tuple[User, Organization, Token]:
        # Check if email is already taken
        existing_user = db.query(User).filter_by(email=reg_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email address already exists."
            )

        # Generate unique slug for the organization
        base_slug = slugify(reg_data.business_name) or "business"
        slug = base_slug
        counter = 1
        while db.query(Organization).filter_by(slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1

        # 1. Create Organization
        org = Organization(
            name=reg_data.business_name,
            slug=slug,
            phone=reg_data.phone,
            timezone=reg_data.timezone or "Asia/Kolkata"
        )
        db.add(org)
        db.flush()  # get org.id

        # 2. Create Owner User
        user = User(
            organization_id=org.id,
            email=reg_data.email,
            hashed_password=get_password_hash(reg_data.password),
            full_name=reg_data.full_name,
            role="owner",
            is_active=True
        )
        db.add(user)
        db.flush()

        # 3. Create default Business Settings
        settings = BusinessSettings(
            organization_id=org.id,
            business_name=reg_data.business_name,
            industry=reg_data.industry or "clinic",
            contact_email=reg_data.email,
            contact_phone=reg_data.phone,
            human_transfer_phone=reg_data.phone,
            default_appointment_duration=30,
            buffer_time_minutes=10,
            max_booking_days_in_advance=30,
            min_booking_notice_hours=2,
            cancellation_notice_hours=4,
            cancellation_policy="Appointments can be rescheduled or cancelled up to 4 hours in advance.",
            ai_greeting_en=f"Hello! Thank you for calling {reg_data.business_name}. I am your AI receptionist. How may I assist you today?",
            ai_greeting_hi=f"नमस्ते! {reg_data.business_name} में कॉल करने के लिए धन्यवाद। मैं आपकी एआई रिसेप्शनिस्ट हूँ। आज मैं आपकी क्या मदद कर सकती हूँ?",
            supported_languages="en,hi",
            prompt_instructions="You are a professional, courteous, and efficient voice receptionist. Always verify customer identity and offer suitable appointment slots."
        )
        db.add(settings)

        # 4. Create default Business Hours:
        # Mon-Fri 09:00 - 18:00, Sat 09:00 - 14:00, Sun Closed
        for day in range(7):
            if day < 5:  # Monday to Friday
                bh = BusinessHours(
                    organization_id=org.id,
                    day_of_week=day,
                    open_time="09:00",
                    close_time="18:00",
                    is_closed=False
                )
            elif day == 5:  # Saturday
                bh = BusinessHours(
                    organization_id=org.id,
                    day_of_week=day,
                    open_time="09:00",
                    close_time="14:00",
                    is_closed=False
                )
            else:  # Sunday
                bh = BusinessHours(
                    organization_id=org.id,
                    day_of_week=day,
                    open_time="00:00",
                    close_time="00:00",
                    is_closed=True
                )
            db.add(bh)

        # 5. Create default starter Service
        default_service = Service(
            organization_id=org.id,
            name="General Consultation",
            description="Initial assessment and consultation service.",
            duration_minutes=30,
            price=500.0,
            currency="INR",
            is_active=True
        )
        db.add(default_service)

        # 6. Create default Staff member
        default_staff = Staff(
            organization_id=org.id,
            name=reg_data.full_name,
            email=reg_data.email,
            phone=reg_data.phone,
            title="Lead Practitioner",
            is_active=True
        )
        db.add(default_staff)

        # 7. Record Audit Log
        audit = AuditLog(
            organization_id=org.id,
            user_id=user.id,
            action="organization_registered",
            entity_type="organization",
            entity_id=org.id,
            details_json=f'{{"name": "{org.name}", "email": "{user.email}"}}'
        )
        db.add(audit)

        db.commit()
        db.refresh(user)
        db.refresh(org)

        tokens = Token(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id)
        )
        return user, org, tokens

    @staticmethod
    def authenticate_user(db: Session, login_data: UserLogin) -> Tuple[User, Organization, Token]:
        user = db.query(User).filter_by(email=login_data.email).first()
        if not user or not verify_password(login_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated."
            )

        org = db.query(Organization).filter_by(id=user.organization_id).first()
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found."
            )

        tokens = Token(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id)
        )
        return user, org, tokens

    @staticmethod
    def refresh_token(db: Session, refresh_token_str: str) -> Token:
        payload = decode_token(refresh_token_str)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token."
            )
        user_id = payload.get("sub")
        user = db.query(User).filter_by(id=user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User no longer active or exists."
            )

        return Token(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id)
        )
