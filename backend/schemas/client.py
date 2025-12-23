from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class ClientBase(BaseModel):
    username: str
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    role: str = "client"


class ClientCreate(ClientBase):
    password: str


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class ClientPasswordUpdate(BaseModel):
    current_password: str
    new_password: str


class ClientResponse(ClientBase):
    client_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ClientLoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    client_id: int
    username: str
    name: str
    role: str


class ClientListResponse(BaseModel):
    client_id: int
    name: str
    username: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    role: str
    is_active: bool

    class Config:
        from_attributes = True
