from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.models.database import get_db
from backend.models.models import Owner, Client
from backend.schemas.owner import OwnerCreate, OwnerUpdate, OwnerResponse
from backend.auth.auth import get_current_user

router = APIRouter(prefix="/api/owners", tags=["owners"])


@router.get("/", response_model=List[OwnerResponse])
def get_owners(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    client_id: Optional[int] = None,
    current_user: Client = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all owners with pagination and search (filtered by client for non-admin)"""
    query = db.query(Owner)

    # Filter by client - admins can see all or filter by client_id, clients see only their own
    if current_user.role != "admin":
        query = query.filter(Owner.client_id == current_user.client_id)
    elif client_id:
        query = query.filter(Owner.client_id == client_id)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Owner.name.like(search_term)) |
            (Owner.email.like(search_term)) |
            (Owner.phone.like(search_term))
        )

    owners = query.offset(skip).limit(limit).all()
    return owners


@router.get("/{owner_id}", response_model=OwnerResponse)
def get_owner(
    owner_id: int,
    current_user: Client = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get owner by ID"""
    owner = db.query(Owner).filter(Owner.owner_id == owner_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Owner not found")

    # Check access permission
    if current_user.role != "admin" and owner.client_id != current_user.client_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return owner


@router.post("/", response_model=OwnerResponse, status_code=201)
def create_owner(
    owner: OwnerCreate,
    current_user: Client = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new owner"""
    # Set client_id from authenticated user if not provided (or if not admin)
    owner_data = owner.model_dump()
    if current_user.role != "admin" or not owner_data.get("client_id"):
        owner_data["client_id"] = current_user.client_id

    # Check if email already exists for the same client
    existing_owner = db.query(Owner).filter(
        Owner.email == owner.email,
        Owner.client_id == owner_data["client_id"]
    ).first()
    if existing_owner:
        raise HTTPException(status_code=400, detail="Email already registered")

    db_owner = Owner(**owner_data)
    db.add(db_owner)
    db.commit()
    db.refresh(db_owner)
    return db_owner


@router.put("/{owner_id}", response_model=OwnerResponse)
def update_owner(
    owner_id: int,
    owner_update: OwnerUpdate,
    current_user: Client = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update owner information"""
    db_owner = db.query(Owner).filter(Owner.owner_id == owner_id).first()
    if not db_owner:
        raise HTTPException(status_code=404, detail="Owner not found")

    # Check access permission
    if current_user.role != "admin" and db_owner.client_id != current_user.client_id:
        raise HTTPException(status_code=403, detail="Access denied")

    update_data = owner_update.model_dump(exclude_unset=True)

    # Check email uniqueness if updating email (scoped to same client)
    if "email" in update_data and update_data["email"] != db_owner.email:
        existing_owner = db.query(Owner).filter(
            Owner.email == update_data["email"],
            Owner.client_id == db_owner.client_id,
            Owner.owner_id != owner_id
        ).first()
        if existing_owner:
            raise HTTPException(status_code=400, detail="Email already registered")

    for field, value in update_data.items():
        setattr(db_owner, field, value)

    db.commit()
    db.refresh(db_owner)
    return db_owner


@router.delete("/{owner_id}", status_code=204)
def delete_owner(
    owner_id: int,
    current_user: Client = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an owner"""
    db_owner = db.query(Owner).filter(Owner.owner_id == owner_id).first()
    if not db_owner:
        raise HTTPException(status_code=404, detail="Owner not found")

    # Check access permission
    if current_user.role != "admin" and db_owner.client_id != current_user.client_id:
        raise HTTPException(status_code=403, detail="Access denied")

    db.delete(db_owner)
    db.commit()
    return None

