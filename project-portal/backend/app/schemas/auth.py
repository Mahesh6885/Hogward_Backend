"""Pydantic schemas for authentication."""
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str  # accepts username OR email
    password: str


class TokenData(BaseModel):
    user_id: int
    username: str
    role: str


class LoginResponseUser(BaseModel):
    id: int
    name: str
    username: str
    role: str
    domain: str | None

    model_config = {"from_attributes": True}


class LoginResponseData(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: LoginResponseUser


class LoginResponse(BaseModel):
    success: bool
    message: str
    data: LoginResponseData


class MeResponse(BaseModel):
    success: bool
    message: str
    data: LoginResponseUser
