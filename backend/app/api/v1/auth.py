from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth import (
    UserRegister, UserLogin, TokenRefresh, AuthResponse, Token,
    CurrentUserWithOrg, UserResponse, OrganizationResponse
)
from app.services.auth_service import AuthService
from app.core.deps import get_current_user, get_current_org
from app.models import User, Organization

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(reg_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new business organization along with its owner user account."""
    user, org, tokens = AuthService.register_business(db, reg_data)
    return AuthResponse(
        user=UserResponse.model_validate(user),
        organization=OrganizationResponse.model_validate(org),
        token=tokens
    )


@router.post("/login", response_model=AuthResponse)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user credentials and receive access + refresh tokens."""
    user, org, tokens = AuthService.authenticate_user(db, login_data)
    return AuthResponse(
        user=UserResponse.model_validate(user),
        organization=OrganizationResponse.model_validate(org),
        token=tokens
    )


@router.post("/refresh", response_model=Token)
def refresh_token(token_data: TokenRefresh, db: Session = Depends(get_db)):
    """Generate a new access token using a valid refresh token."""
    return AuthService.refresh_token(db, token_data.refresh_token)


@router.get("/me", response_model=CurrentUserWithOrg)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org)
):
    """Retrieve details of the currently authenticated user and active organization."""
    return CurrentUserWithOrg(
        user=UserResponse.model_validate(current_user),
        organization=OrganizationResponse.model_validate(current_org)
    )
