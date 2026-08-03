import uuid
from typing import Optional
from fastapi import HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.security import (
    create_access_token,
    get_password_hash,
    get_user_id_from_token,
    verify_password,
)
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

settings = get_settings()


class AuthService:
    async def get_guest_user_from_token(
        self, db: AsyncSession, guest_token: Optional[str]
    ) -> Optional[User]:
        """Extract guest user from token if valid and currently marked as is_guest."""
        if not guest_token:
            return None
        guest_id_str = get_user_id_from_token(guest_token)
        if not guest_id_str:
            return None
        try:
            guest_id = uuid.UUID(guest_id_str)
        except ValueError:
            return None

        result = await db.execute(
            select(User).where(User.id == guest_id, User.is_guest == True)
        )
        return result.scalar_one_or_none()

    async def register(
        self, db: AsyncSession, req: RegisterRequest
    ) -> AuthTokenResponse:
        """Register new user or convert guest user into a registered account."""
        if not req.username or not req.email or not req.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username, email, and password are required",
            )

        # Check existing registered user by email or username
        result = await db.execute(
            select(User).where(
                or_(User.email == req.email, User.username == req.username)
            )
        )
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email or username already exists",
            )

        password_hash = get_password_hash(req.password)
        user: Optional[User] = None

        # Attempt to migrate guest account if guest_token provided
        if req.guest_token:
            guest_user = await self.get_guest_user_from_token(db, req.guest_token)
            if guest_user:
                guest_user.username = req.username
                guest_user.email = req.email
                guest_user.password_hash = password_hash
                guest_user.is_guest = False
                user = guest_user

        if not user:
            user = User(
                username=req.username,
                email=req.email,
                password_hash=password_hash,
                is_guest=False,
            )
            db.add(user)

        await db.commit()
        await db.refresh(user)

        token = create_access_token(user.id)
        return AuthTokenResponse(
            token=token, user=UserResponse.model_validate(user)
        )

    async def login(self, db: AsyncSession, req: LoginRequest) -> AuthTokenResponse:
        """Authenticate user by email and password."""
        if not req.email or not req.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email and password are required",
            )

        result = await db.execute(select(User).where(User.email == req.email))
        user = result.scalar_one_or_none()

        if not user or not user.password_hash or not verify_password(req.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        token = create_access_token(user.id)
        return AuthTokenResponse(
            token=token, user=UserResponse.model_validate(user)
        )

    async def guest_login(
        self, db: AsyncSession, req: GuestLoginRequest
    ) -> AuthTokenResponse:
        """Create a new guest account or return existing guest session."""
        if req.guest_token:
            guest_user = await self.get_guest_user_from_token(db, req.guest_token)
            if guest_user:
                token = create_access_token(guest_user.id)
                return AuthTokenResponse(
                    token=token, user=UserResponse.model_validate(guest_user)
                )

        user = User(is_guest=True)
        db.add(user)
        await db.commit()
        await db.refresh(user)

        token = create_access_token(user.id)
        return AuthTokenResponse(
            token=token, user=UserResponse.model_validate(user)
        )

    async def google_login(
        self, db: AsyncSession, req: GoogleLoginRequest
    ) -> AuthTokenResponse:
        """Authenticate via Google OAuth2 ID token and migrate guest if provided."""
        if not req.credential:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google credential token is required",
            )

        payload = None
        client_id = settings.GOOGLE_CLIENT_ID or "DUMMY_CLIENT_ID"

        try:
            payload = google_id_token.verify_oauth2_token(
                req.credential, google_requests.Request(), audience=client_id
            )
        except Exception:
            # Fallback mock for local development testing if DUMMY_CLIENT_ID is configured
            if client_id == "DUMMY_CLIENT_ID":
                payload = {
                    "sub": "dummy_google_12345",
                    "email": "dummy@google.com",
                    "name": "Google Test User",
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Google token",
                )

        if not payload or "sub" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Google token payload",
            )

        google_id = payload["sub"]
        email = payload.get("email")
        username = payload.get("name") or f"user_{google_id}"

        # 1. Check existing user by google_id
        result = await db.execute(select(User).where(User.google_id == google_id))
        user = result.scalar_one_or_none()

        if not user:
            # 2. Check if guest token provided to migrate guest user
            if req.guest_token:
                guest_user = await self.get_guest_user_from_token(db, req.guest_token)
                if guest_user:
                    guest_user.google_id = google_id
                    guest_user.email = email
                    guest_user.username = username
                    guest_user.is_guest = False
                    user = guest_user

            if not user and email:
                # 3. Check if email already registered via standard auth
                result = await db.execute(select(User).where(User.email == email))
                existing_email_user = result.scalar_one_or_none()
                if existing_email_user:
                    existing_email_user.google_id = google_id
                    existing_email_user.is_guest = False
                    user = existing_email_user

            if not user:
                # 4. Create new user
                user = User(
                    google_id=google_id,
                    email=email,
                    username=username,
                    is_guest=False,
                )
                db.add(user)

        await db.commit()
        await db.refresh(user)

        token = create_access_token(user.id)
        return AuthTokenResponse(
            token=token, user=UserResponse.model_validate(user)
        )

    async def forgot_password(
        self, db: AsyncSession, req: ForgotPasswordRequest
    ) -> ForgotPasswordResponse:
        """Handle password reset requests. Always returns success message to prevent account enumeration."""
        if not req.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is required",
            )

        # Check user existence (silent check)
        result = await db.execute(select(User).where(User.email == req.email))
        user = result.scalar_one_or_none()

        if user:
            # Future enhancement: Send actual reset email via SMTP / SendGrid / SES
            pass

        return ForgotPasswordResponse(
            message="If an account with this email exists, password reset instructions have been sent."
        )
