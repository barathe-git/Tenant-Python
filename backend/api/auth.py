from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import timedelta

from backend.models.database import get_db
from backend.models.models import Client
from backend.schemas.client import (
    ClientCreate, ClientUpdate, ClientResponse, ClientListResponse,
    ClientLoginRequest, TokenResponse, ClientPasswordUpdate
)
from backend.auth.auth import (
    get_password_hash, authenticate_user, create_access_token,
    get_current_user, get_current_active_admin, ACCESS_TOKEN_EXPIRE_MINUTES,
    verify_password
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(request: ClientLoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token"""
    user = authenticate_user(db, request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role, "client_id": user.client_id},
        expires_delta=access_token_expires
    )

    return TokenResponse(
        access_token=access_token,
        client_id=user.client_id,
        username=user.username,
        name=user.name,
        role=user.role
    )


@router.get("/me", response_model=ClientResponse)
def get_current_user_info(current_user: Client = Depends(get_current_user)):
    """Get current authenticated user information"""
    return current_user


@router.put("/me/password")
def change_password(
    password_update: ClientPasswordUpdate,
    current_user: Client = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change current user's password"""
    if not verify_password(password_update.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    current_user.password_hash = get_password_hash(password_update.new_password)
    db.commit()

    return {"message": "Password updated successfully"}


# Client management endpoints (Admin only)
@router.get("/clients", response_model=List[ClientListResponse])
def get_all_clients(
    skip: int = 0,
    limit: int = 100,
    current_user: Client = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Get all clients (Admin only)"""
    clients = db.query(Client).offset(skip).limit(limit).all()
    return clients


@router.post("/clients", response_model=ClientResponse)
def create_client(
    client: ClientCreate,
    current_user: Client = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Create a new client (Admin only)"""
    # Check if username already exists
    existing = db.query(Client).filter(Client.username == client.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    db_client = Client(
        username=client.username,
        password_hash=get_password_hash(client.password),
        name=client.name,
        email=client.email,
        phone=client.phone,
        role=client.role
    )
    db.add(db_client)
    db.commit()
    db.refresh(db_client)

    return db_client


@router.get("/clients/{client_id}", response_model=ClientResponse)
def get_client(
    client_id: int,
    current_user: Client = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Get a specific client (Admin only)"""
    client = db.query(Client).filter(Client.client_id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.put("/clients/{client_id}", response_model=ClientResponse)
def update_client(
    client_id: int,
    client_update: ClientUpdate,
    current_user: Client = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Update a client (Admin only)"""
    client = db.query(Client).filter(Client.client_id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    update_data = client_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(client, key, value)

    db.commit()
    db.refresh(client)

    return client


@router.delete("/clients/{client_id}")
def delete_client(
    client_id: int,
    current_user: Client = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Delete a client (Admin only)"""
    client = db.query(Client).filter(Client.client_id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    if client.client_id == current_user.client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    db.delete(client)
    db.commit()

    return {"message": "Client deleted successfully"}


@router.post("/clients/{client_id}/reset-password")
def reset_client_password(
    client_id: int,
    new_password: str,
    current_user: Client = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Reset a client's password (Admin only)"""
    client = db.query(Client).filter(Client.client_id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    client.password_hash = get_password_hash(new_password)
    db.commit()

    return {"message": "Password reset successfully"}


# Initial setup endpoint (only works when no admin exists)
@router.post("/setup", response_model=ClientResponse)
def initial_setup(client: ClientCreate, db: Session = Depends(get_db)):
    """Create the initial admin account (only works if no admin exists)"""
    # Check if any admin exists
    admin_exists = db.query(Client).filter(Client.role == "admin").first()
    if admin_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Initial setup already completed. Please login."
        )

    # Create admin account
    db_client = Client(
        username=client.username,
        password_hash=get_password_hash(client.password),
        name=client.name,
        email=client.email,
        phone=client.phone,
        role="admin"  # Force admin role for initial setup
    )
    db.add(db_client)
    db.commit()
    db.refresh(db_client)

    return db_client
