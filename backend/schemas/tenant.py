from pydantic import BaseModel, EmailStr, computed_field
from typing import Optional
from datetime import date, datetime


class TenantBase(BaseModel):
    name: str
    phone: str
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    portion_number: str
    rent_amount: float = 0
    water_charge: float = 0
    maintenance_charge: float = 0
    advance_amount: float = 0
    rent_due_date: int = 1  # Day of month (1-28) when rent is due
    agreement_start_date: date
    agreement_end_date: date
    aadhar_number: Optional[str] = None


class TenantCreate(TenantBase):
    building_id: int
    owner_id: int
    agreement_pdf_path: Optional[str] = None
    aadhar_pdf_path: Optional[str] = None


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    portion_number: Optional[str] = None
    rent_amount: Optional[float] = None
    water_charge: Optional[float] = None
    maintenance_charge: Optional[float] = None
    advance_amount: Optional[float] = None
    rent_due_date: Optional[int] = None
    agreement_start_date: Optional[date] = None
    agreement_end_date: Optional[date] = None
    agreement_pdf_path: Optional[str] = None
    aadhar_number: Optional[str] = None
    aadhar_pdf_path: Optional[str] = None


class TenantResponse(TenantBase):
    tenant_id: int
    building_id: int
    owner_id: int
    agreement_pdf_path: Optional[str] = None
    aadhar_pdf_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def total_rent(self) -> float:
        return (self.rent_amount or 0) + (self.water_charge or 0) + (self.maintenance_charge or 0)

    class Config:
        from_attributes = True

