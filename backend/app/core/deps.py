from typing import Optional, List, Callable
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.security import decode_token
from app.models import User, Organization, BusinessSettings
from app.config import settings
import os

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False)


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Handle demo bypass token
    if token == "demo_token_bypass":
        org = db.query(Organization).first()
        if not org:
            org = Organization(
                id="61f4e93d-706e-4ab4-92d9-63d882c4b8fd",
                name="Apex Dental Clinic",
                slug="apex-dental-clinic",
                timezone="Asia/Kolkata"
            )
            db.add(org)
            db.flush()
        user = db.query(User).filter_by(organization_id=org.id).first()
        if not user:
            user = User(
                id="demo-user-1",
                organization_id=org.id,
                email="admin@apexdental.com",
                hashed_password="ephemeral_session_pwd",
                full_name="Dr. John Smith",
                role="owner",
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    payload = decode_token(token)
    user_id: Optional[str] = payload.get("sub")
    token_type: Optional[str] = payload.get("type")
    
    if user_id is None or token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter_by(id=user_id).first()
    if user is None:
        # In serverless ephemeral SQLite environments, re-create the user if the container recycled
        if settings.DATABASE_URL.startswith("sqlite") or os.environ.get("VERCEL"):
            org = db.query(Organization).first()
            if not org:
                org = Organization(
                    id="61f4e93d-706e-4ab4-92d9-63d882c4b8fd",
                    name="Apex Dental Clinic",
                    slug="apex-dental-clinic",
                    timezone="Asia/Kolkata"
                )
                db.add(org)
                db.flush()
                settings_rec = BusinessSettings(
                    organization_id=org.id,
                    business_name=org.name,
                    industry="clinic",
                    ai_greeting_en=f"Hello, thank you for calling {org.name}. How may I help you today?",
                    ai_greeting_hi=f"Namaste, {org.name} me aapka swagat hai. Main aapki kya sahayata kar sakta hoon?",
                    human_transfer_phone="+919876543210",
                    supported_languages="en,hi"
                )
                db.add(settings_rec)
                db.flush()

            user = User(
                id=user_id,
                organization_id=org.id,
                email="admin@apexdental.com",
                hashed_password="ephemeral_session_pwd",
                full_name="Dr. John Smith",
                role="owner",
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found."
            )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user."
        )
    return user


def get_current_org(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Organization:
    """
    Enforces tenant isolation by strictly deriving organization from authenticated user context.
    Never accepts arbitrary organization_id from user inputs.
    """
    org = db.query(Organization).filter_by(id=current_user.organization_id).first()
    if not org:
        if settings.DATABASE_URL.startswith("sqlite") or os.environ.get("VERCEL"):
            org = Organization(
                id=current_user.organization_id,
                name="Apex Dental Clinic",
                slug=f"org-{current_user.organization_id[:8]}",
                timezone="Asia/Kolkata"
            )
            db.add(org)
            db.commit()
            db.refresh(org)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found for current user."
            )
    return org


def require_roles(allowed_roles: List[str]) -> Callable:
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Requires one of roles: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker


def verify_vapi_secret(
    x_vapi_secret: Optional[str] = Header(None, alias="x-vapi-secret")
) -> bool:
    """
    Validates webhook requests from Vapi via shared secret header.
    """
    if not settings.VAPI_WEBHOOK_SECRET:
        return True  # If not configured, allow in dev
    
    if x_vapi_secret != settings.VAPI_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing Vapi webhook secret."
        )
    return True
