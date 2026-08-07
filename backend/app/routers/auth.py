from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user
from app.core.net import get_client_ip
from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    AuthTokenResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    GoogleLoginRequest,
    GuestLoginRequest,
    LoginRequest,
    RegisterRequest,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
auth_service = AuthService()


@router.post("/register", response_model=AuthTokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    req: RegisterRequest, db: AsyncSession = Depends(get_db)
):
    return await auth_service.register(db, req)


@router.post("/login", response_model=AuthTokenResponse)
async def login(
    req: LoginRequest, db: AsyncSession = Depends(get_db)
):
    return await auth_service.login(db, req)


@router.post("/guest", response_model=AuthTokenResponse, status_code=status.HTTP_201_CREATED)
async def guest_login(
    request: Request,
    req: GuestLoginRequest = GuestLoginRequest(),
    db: AsyncSession = Depends(get_db),
):
    return await auth_service.guest_login(db, req, client_ip=get_client_ip(request))


@router.post("/google", response_model=AuthTokenResponse)
async def google_login(
    req: GoogleLoginRequest, db: AsyncSession = Depends(get_db)
):
    return await auth_service.google_login(db, req)


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    req: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)
):
    return await auth_service.forgot_password(db, req)


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    return UserResponse.model_validate(current_user)
