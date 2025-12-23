from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, timedelta
from backend.models.database import get_db
from backend.models.models import Tenant, Building, Owner, Client
from backend.schemas.tenant import TenantCreate, TenantUpdate, TenantResponse
from backend.auth.auth import get_current_user

router = APIRouter(prefix="/api/tenants", tags=["tenants"])


@router.get("/", response_model=List[TenantResponse])
def get_tenants(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    building_id: Optional[int] = None,
    owner_id: Optional[int] = None,
    client_id: Optional[int] = None,
    search: Optional[str] = None,
    current_user: Client = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all tenants with pagination and filters (filtered by client for non-admin)"""
    query = db.query(Tenant).join(Owner, Tenant.owner_id == Owner.owner_id)

    # Filter by client - admins can see all or filter by client_id, clients see only their own
    if current_user.role != "admin":
        query = query.filter(Owner.client_id == current_user.client_id)
    elif client_id:
        query = query.filter(Owner.client_id == client_id)

    if building_id:
        query = query.filter(Tenant.building_id == building_id)

    if owner_id:
        query = query.filter(Tenant.owner_id == owner_id)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Tenant.name.like(search_term)) |
            (Tenant.email.like(search_term)) |
            (Tenant.phone.like(search_term)) |
            (Tenant.portion_number.like(search_term))
        )

    tenants = query.offset(skip).limit(limit).all()
    return tenants


@router.get("/building/{building_id}", response_model=List[TenantResponse])
def get_tenants_by_building(
    building_id: int,
    current_user: Client = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all tenants for a specific building"""
    building = db.query(Building).filter(Building.building_id == building_id).first()
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")

    # Check access permission
    owner = db.query(Owner).filter(Owner.owner_id == building.owner_id).first()
    if current_user.role != "admin" and owner.client_id != current_user.client_id:
        raise HTTPException(status_code=403, detail="Access denied")

    tenants = db.query(Tenant).filter(Tenant.building_id == building_id).all()
    return tenants


@router.get("/expiring", response_model=List[TenantResponse])
def get_expiring_tenants(
    days: int = Query(30, ge=1, le=365),
    client_id: Optional[int] = None,
    current_user: Client = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get tenants with agreements expiring within specified days"""
    today = date.today()
    expiry_date = today + timedelta(days=days)

    query = db.query(Tenant).join(Owner, Tenant.owner_id == Owner.owner_id).filter(
        Tenant.agreement_end_date >= today,
        Tenant.agreement_end_date <= expiry_date
    )

    # Filter by client - admins can see all or filter by client_id, clients see only their own
    if current_user.role != "admin":
        query = query.filter(Owner.client_id == current_user.client_id)
    elif client_id:
        query = query.filter(Owner.client_id == client_id)

    tenants = query.order_by(Tenant.agreement_end_date).all()
    return tenants


@router.get("/{tenant_id}", response_model=TenantResponse)
def get_tenant(
    tenant_id: int,
    current_user: Client = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get tenant by ID"""
    tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Check access permission
    owner = db.query(Owner).filter(Owner.owner_id == tenant.owner_id).first()
    if current_user.role != "admin" and owner.client_id != current_user.client_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return tenant


@router.post("/", response_model=TenantResponse, status_code=201)
def create_tenant(
    tenant: TenantCreate,
    current_user: Client = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new tenant"""
    # Verify owner exists
    owner = db.query(Owner).filter(Owner.owner_id == tenant.owner_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Owner not found")

    # Check access permission
    if current_user.role != "admin" and owner.client_id != current_user.client_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Verify building exists
    building = db.query(Building).filter(Building.building_id == tenant.building_id).first()
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")

    # Verify building belongs to owner
    if building.owner_id != tenant.owner_id:
        raise HTTPException(status_code=400, detail="Building does not belong to the specified owner")

    # Validate dates
    if tenant.agreement_start_date >= tenant.agreement_end_date:
        raise HTTPException(status_code=400, detail="Agreement end date must be after start date")

    db_tenant = Tenant(**tenant.model_dump())
    db.add(db_tenant)
    db.commit()
    db.refresh(db_tenant)
    return db_tenant


@router.put("/{tenant_id}", response_model=TenantResponse)
def update_tenant(
    tenant_id: int,
    tenant_update: TenantUpdate,
    current_user: Client = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update tenant information"""
    db_tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
    if not db_tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Check access permission
    owner = db.query(Owner).filter(Owner.owner_id == db_tenant.owner_id).first()
    if current_user.role != "admin" and owner.client_id != current_user.client_id:
        raise HTTPException(status_code=403, detail="Access denied")

    update_data = tenant_update.model_dump(exclude_unset=True)

    # Validate dates if both are being updated
    if "agreement_start_date" in update_data or "agreement_end_date" in update_data:
        start_date = update_data.get("agreement_start_date", db_tenant.agreement_start_date)
        end_date = update_data.get("agreement_end_date", db_tenant.agreement_end_date)
        if start_date >= end_date:
            raise HTTPException(status_code=400, detail="Agreement end date must be after start date")

    for field, value in update_data.items():
        setattr(db_tenant, field, value)

    db.commit()
    db.refresh(db_tenant)
    return db_tenant


@router.delete("/{tenant_id}", status_code=204)
def delete_tenant(
    tenant_id: int,
    current_user: Client = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a tenant"""
    db_tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
    if not db_tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Check access permission
    owner = db.query(Owner).filter(Owner.owner_id == db_tenant.owner_id).first()
    if current_user.role != "admin" and owner.client_id != current_user.client_id:
        raise HTTPException(status_code=403, detail="Access denied")

    db.delete(db_tenant)
    db.commit()
    return None
