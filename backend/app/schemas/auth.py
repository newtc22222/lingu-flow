import uuid
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    guest_token: Optional[str] = Field(default=None, alias="guestToken")

    model_config = ConfigDict(populate_by_name=True)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    model_config = ConfigDict(populate_by_name=True)


class GuestLoginRequest(BaseModel):
    guest_token: Optional[str] = Field(default=None, alias="guestToken")

    model_config = ConfigDict(populate_by_name=True)


class GoogleLoginRequest(BaseModel):
    credential: str
    guest_token: Optional[str] = Field(default=None, alias="guestToken")

    model_config = ConfigDict(populate_by_name=True)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr

    model_config = ConfigDict(populate_by_name=True)


class ForgotPasswordResponse(BaseModel):
    message: str

    model_config = ConfigDict(populate_by_name=True)


class UserResponse(BaseModel):
    id: uuid.UUID
    username: Optional[str] = None
    email: Optional[str] = None
    is_guest: bool = Field(default=False, alias="isGuest")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class AuthTokenResponse(BaseModel):
    token: str
    user: UserResponse

    model_config = ConfigDict(populate_by_name=True)
