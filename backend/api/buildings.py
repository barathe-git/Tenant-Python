from enum import Enum
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from backend.models.database import get_db
from backend.models.models import Building, Owner, Client
from backend.schemas.building import BuildingCreate, BuildingUpdate, BuildingResponse
from backend.auth.auth import get_current_user

router = APIRouter(prefix="/api/buildings", tags=["buildings"])


@router.get("/", response_model=List[BuildingResponse])
def get_buildings(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    owner_id: Optional[int] = None,
    building_type: Optional[str] = None,
    client_id: Optional[int] = None,
    current_user: Client = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all buildings with pagination and filters (filtered by client for non-admin)"""
    # Use raw SQL to avoid enum conversion issues
    query_sql = """
        SELECT
            b.building_id,
            b.owner_id,
            b.building_name,
            CAST(b.building_type AS CHAR) as building_type,
            b.number_of_portions,
            b.location,
            b.created_at,
            b.updated_at
        FROM buildings b
        JOIN owners o ON b.owner_id = o.owner_id
        WHERE 1=1
    """
    params = {}

    # Filter by client - admins can see all or filter by client_id, clients see only their own
    if current_user.role != "admin":
        query_sql += " AND o.client_id = :client_id"
        params['client_id'] = current_user.client_id
    elif client_id:
        query_sql += " AND o.client_id = :client_id"
        params['client_id'] = client_id

    if owner_id:
        query_sql += " AND b.owner_id = :owner_id"
        params['owner_id'] = owner_id

    if building_type:
        # Validate building type
        if building_type in ['Residence', 'Commercial']:
            query_sql += " AND b.building_type = :building_type"
            params['building_type'] = building_type
        # If invalid, just ignore the filter

    query_sql += " LIMIT :limit OFFSET :offset"
    params['limit'] = limit
    params['offset'] = skip

    # Use raw connection to completely bypass SQLAlchemy enum processing
    from backend.models.database import engine

    # Convert to response format
    result = []
    with engine.connect() as connection:
        # Use mappings() to get dict-like rows without type conversion
        result_proxy = connection.execute(text(query_sql), params)
        result_rows = result_proxy.mappings().fetchall()

        for row in result_rows:
            # Access row as dict (already converted by mappings())
            # Handle building_type - it's already a string from CAST
            building_type_str = str(row['building_type']).strip() if row['building_type'] else 'Residence'
            if building_type_str not in ['Residence', 'Commercial']:
                building_type_str = 'Residence'

            building_dict = {
                "building_id": row['building_id'],
                "owner_id": row['owner_id'],
                "building_name": row['building_name'],
                "building_type": building_type_str,
                "number_of_portions": row['number_of_portions'],
                "location": row['location'],
                "created_at": row['created_at'],
                "updated_at": row['updated_at']
            }
            result.append(building_dict)

    return result


@router.get("/owner/{owner_id}", response_model=List[BuildingResponse])
def get_buildings_by_owner(
    owner_id: int,
    current_user: Client = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all buildings for a specific owner"""
    owner = db.query(Owner).filter(Owner.owner_id == owner_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Owner not found")

    # Check access permission
    if current_user.role != "admin" and owner.client_id != current_user.client_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Use raw SQL to avoid enum conversion issues
    from sqlalchemy import text
    from backend.models.database import engine
    
    query_sql = text("""
        SELECT 
            building_id,
            owner_id,
            building_name,
            building_type,
            number_of_portions,
            location,
            created_at,
            updated_at
        FROM buildings
        WHERE owner_id = :owner_id
    """)
    
    # Get column names
    columns = ['building_id', 'owner_id', 'building_name', 'building_type', 
               'number_of_portions', 'location', 'created_at', 'updated_at']
    
    # Convert to response format
    result = []
    # Use raw connection to completely bypass SQLAlchemy enum processing
    with engine.connect() as connection:
        result_proxy = connection.execute(query_sql, {"owner_id": owner_id})
        result_rows = result_proxy.mappings().fetchall()
        
        for row in result_rows:
            # Access row as dict (already converted by mappings())
            building_type_str = str(row['building_type']).strip() if row['building_type'] else 'Residence'
            if building_type_str not in ['Residence', 'Commercial']:
                building_type_str = 'Residence'
            
            building_dict = {
                "building_id": row['building_id'],
                "owner_id": row['owner_id'],
                "building_name": row['building_name'],
                "building_type": building_type_str,
                "number_of_portions": row['number_of_portions'],
                "location": row['location'],
                "created_at": row['created_at'],
                "updated_at": row['updated_at']
            }
            result.append(building_dict)
    
    return result


@router.get("/{building_id}", response_model=BuildingResponse)
def get_building(
    building_id: int,
    current_user: Client = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get building by ID"""
    from sqlalchemy import text
    
    query_sql = text("""
        SELECT 
            building_id,
            owner_id,
            building_name,
            building_type,
            number_of_portions,
            location,
            created_at,
            updated_at
        FROM buildings
        WHERE building_id = :building_id
    """)
    
    # Use raw connection to completely bypass SQLAlchemy enum processing
    from backend.models.database import engine
    
    # Get column names
    columns = ['building_id', 'owner_id', 'building_name', 'building_type', 
               'number_of_portions', 'location', 'created_at', 'updated_at']
    
    with engine.connect() as connection:
        result_proxy = connection.execute(query_sql, {"building_id": building_id})
        row = result_proxy.mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="Building not found")
        
        # Access row as dict (already converted by mappings())
        # Handle enum conversion
        building_type_str = str(row['building_type']).strip() if row['building_type'] else 'Residence'
        if building_type_str not in ['Residence', 'Commercial']:
            building_type_str = 'Residence'
        
        building_dict = {
            "building_id": row['building_id'],
            "owner_id": row['owner_id'],
            "building_name": row['building_name'],
            "building_type": building_type_str,
            "number_of_portions": row['number_of_portions'],
            "location": row['location'],
            "created_at": row['created_at'],
            "updated_at": row['updated_at']
        }
        return building_dict


@router.post("/", response_model=BuildingResponse, status_code=201)
def create_building(
    building: BuildingCreate,
    current_user: Client = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new building"""
    # Verify owner exists
    owner = db.query(Owner).filter(Owner.owner_id == building.owner_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Owner not found")

    # Check access permission
    if current_user.role != "admin" and owner.client_id != current_user.client_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Validate building type
    building_type_str = building.building_type
    if building_type_str not in ['Residence', 'Commercial']:
        raise HTTPException(status_code=400, detail="Invalid building type. Must be 'Residence' or 'Commercial'")
    
    db_building = Building(
        owner_id=building.owner_id,
        building_name=building.building_name,
        building_type=building_type_str,
        number_of_portions=building.number_of_portions,
        location=building.location
    )
    db.add(db_building)
    db.commit()
    db.refresh(db_building)
    # Convert enum to string for response
    building_dict = {
        "building_id": db_building.building_id,
        "owner_id": db_building.owner_id,
        "building_name": db_building.building_name,
        "building_type": db_building.building_type.value if isinstance(db_building.building_type, Enum) else db_building.building_type,
        "number_of_portions": db_building.number_of_portions,
        "location": db_building.location,
        "created_at": db_building.created_at,
        "updated_at": db_building.updated_at
    }
    return building_dict


@router.put("/{building_id}", response_model=BuildingResponse)
def update_building(
    building_id: int,
    building_update: BuildingUpdate,
    current_user: Client = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update building information"""
    db_building = db.query(Building).filter(Building.building_id == building_id).first()
    if not db_building:
        raise HTTPException(status_code=404, detail="Building not found")

    # Check access permission
    owner = db.query(Owner).filter(Owner.owner_id == db_building.owner_id).first()
    if current_user.role != "admin" and owner.client_id != current_user.client_id:
        raise HTTPException(status_code=403, detail="Access denied")

    update_data = building_update.model_dump(exclude_unset=True)
    
    # Validate building type if updating
    if "building_type" in update_data:
        building_type_str = update_data["building_type"]
        if building_type_str not in ['Residence', 'Commercial']:
            raise HTTPException(status_code=400, detail="Invalid building type. Must be 'Residence' or 'Commercial'")
        # Keep as string, no conversion needed
    
    for field, value in update_data.items():
        setattr(db_building, field, value)
    
    db.commit()
    db.refresh(db_building)
    # Convert enum to string for response
    building_dict = {
        "building_id": db_building.building_id,
        "owner_id": db_building.owner_id,
        "building_name": db_building.building_name,
        "building_type": db_building.building_type.value if isinstance(db_building.building_type, BuildingType) else str(db_building.building_type),
        "number_of_portions": db_building.number_of_portions,
        "location": db_building.location,
        "created_at": db_building.created_at,
        "updated_at": db_building.updated_at
    }
    return building_dict


@router.delete("/{building_id}", status_code=204)
def delete_building(
    building_id: int,
    current_user: Client = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a building"""
    db_building = db.query(Building).filter(Building.building_id == building_id).first()
    if not db_building:
        raise HTTPException(status_code=404, detail="Building not found")

    # Check access permission
    owner = db.query(Owner).filter(Owner.owner_id == db_building.owner_id).first()
    if current_user.role != "admin" and owner.client_id != current_user.client_id:
        raise HTTPException(status_code=403, detail="Access denied")

    db.delete(db_building)
    db.commit()
    return None

