from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class BuildingBase(BaseModel):
    building_name: str
    building_type: str  # "Residence" or "Commercial"
    number_of_portions: int
    location: Optional[str] = None


class BuildingCreate(BuildingBase):
    owner_id: int


class BuildingUpdate(BaseModel):
    building_name: Optional[str] = None
    building_type: Optional[str] = None
    number_of_portions: Optional[int] = None
    location: Optional[str] = None


class BuildingResponse(BuildingBase):
    building_id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

