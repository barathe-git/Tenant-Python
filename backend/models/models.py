from sqlalchemy import Column, Integer, String, Text, Date, Numeric, Enum, Boolean, ForeignKey, TIMESTAMP, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
import enum


class BuildingType(enum.Enum):
    RESIDENCE = "Residence"
    COMMERCIAL = "Commercial"


class UserRole(enum.Enum):
    ADMIN = "admin"
    CLIENT = "client"


class Client(Base):
    """Client entity - represents separate clients like Elumalai, Saritha etc."""
    __tablename__ = "clients"

    client_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), index=True)
    phone = Column(String(20))
    role = Column(String(20), nullable=False, default='client')  # 'admin' or 'client'
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relationships
    owners = relationship("Owner", back_populates="client", cascade="all, delete-orphan")


class Owner(Base):
    __tablename__ = "owners"

    owner_id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.client_id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    address = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relationships
    client = relationship("Client", back_populates="owners")
    buildings = relationship("Building", back_populates="owner", cascade="all, delete-orphan")
    tenants = relationship("Tenant", back_populates="owner", cascade="all, delete-orphan")


class Building(Base):
    __tablename__ = "buildings"

    building_id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("owners.owner_id", ondelete="CASCADE"), nullable=False, index=True)
    building_name = Column(String(255), nullable=False)
    building_type = Column(String(20), nullable=False, default='Residence', index=True)
    number_of_portions = Column(Integer, nullable=False, default=1)
    location = Column(String(500))
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relationships
    owner = relationship("Owner", back_populates="buildings")
    tenants = relationship("Tenant", back_populates="building", cascade="all, delete-orphan")


class Tenant(Base):
    __tablename__ = "tenants"

    tenant_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(255), index=True)
    portion_number = Column(String(50), nullable=False)
    # Separated rent components
    rent_amount = Column(Numeric(10, 2), nullable=False, default=0)  # Base rent
    water_charge = Column(Numeric(10, 2), nullable=False, default=0)
    maintenance_charge = Column(Numeric(10, 2), nullable=False, default=0)
    advance_amount = Column(Numeric(10, 2), nullable=False, default=0)
    rent_due_date = Column(Integer, nullable=False, default=1)  # Day of month (1-28) when rent is due
    agreement_start_date = Column(Date, nullable=False)
    agreement_end_date = Column(Date, nullable=False, index=True)
    building_id = Column(Integer, ForeignKey("buildings.building_id", ondelete="CASCADE"), nullable=False, index=True)
    owner_id = Column(Integer, ForeignKey("owners.owner_id", ondelete="CASCADE"), nullable=False, index=True)
    agreement_pdf_path = Column(String(500))
    aadhar_number = Column(String(12))
    aadhar_pdf_path = Column(String(500))
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relationships
    owner = relationship("Owner", back_populates="tenants")
    building = relationship("Building", back_populates="tenants")
    alerts = relationship("Alert", back_populates="tenant", cascade="all, delete-orphan")

    @property
    def total_rent(self):
        """Calculate total rent including all charges"""
        return float(self.rent_amount or 0) + float(self.water_charge or 0) + float(self.maintenance_charge or 0)


class Alert(Base):
    __tablename__ = "alerts"

    alert_id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.tenant_id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_name = Column(String(255), nullable=False)
    building_name = Column(String(255), nullable=False)
    agreement_end_date = Column(Date, nullable=False, index=True)
    days_remaining = Column(Integer, nullable=False)
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    tenant = relationship("Tenant", back_populates="alerts")

