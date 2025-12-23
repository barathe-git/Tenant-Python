from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class OwnerBase(BaseModel):
    name: str
    phone: str
    email: EmailStr
    address: Optional[str] = None


class OwnerCreate(OwnerBase):
    client_id: Optional[int] = None  # Will be set from authenticated user if not provided


class OwnerUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None


class OwnerResponse(OwnerBase):
    owner_id: int
    client_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

