from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from typing import Optional
from datetime import date, timedelta
from backend.models.database import get_db, engine
from backend.models.models import Owner, Building, Tenant, Client
from backend.auth.auth import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats")
def get_dashboard_stats(
    client_id: Optional[int] = None,
    current_user: Client = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics (filtered by client for non-admin)"""

    # Determine client filter
    filter_client_id = None
    if current_user.role != "admin":
        filter_client_id = current_user.client_id
    elif client_id:
        filter_client_id = client_id

    # Total counts with client filter
    if filter_client_id:
        total_owners = db.query(func.count(Owner.owner_id)).filter(
            Owner.client_id == filter_client_id
        ).scalar() or 0

        total_buildings = db.query(func.count(Building.building_id)).join(
            Owner, Building.owner_id == Owner.owner_id
        ).filter(Owner.client_id == filter_client_id).scalar() or 0

        total_tenants = db.query(func.count(Tenant.tenant_id)).join(
            Owner, Tenant.owner_id == Owner.owner_id
        ).filter(Owner.client_id == filter_client_id).scalar() or 0
    else:
        total_owners = db.query(func.count(Owner.owner_id)).scalar() or 0
        total_buildings = db.query(func.count(Building.building_id)).scalar() or 0
        total_tenants = db.query(func.count(Tenant.tenant_id)).scalar() or 0

    # Expiring agreements (next 30 days)
    today = date.today()
    expiry_date = today + timedelta(days=30)

    if filter_client_id:
        expiring_agreements = db.query(func.count(Tenant.tenant_id)).join(
            Owner, Tenant.owner_id == Owner.owner_id
        ).filter(
            Owner.client_id == filter_client_id,
            Tenant.agreement_end_date >= today,
            Tenant.agreement_end_date <= expiry_date
        ).scalar() or 0
    else:
        expiring_agreements = db.query(func.count(Tenant.tenant_id)).filter(
            Tenant.agreement_end_date >= today,
            Tenant.agreement_end_date <= expiry_date
        ).scalar() or 0

    # Building occupancy - get all buildings first, then count tenants per building
    if filter_client_id:
        buildings_query = db.query(Building).join(
            Owner, Building.owner_id == Owner.owner_id
        ).filter(Owner.client_id == filter_client_id).all()
    else:
        buildings_query = db.query(Building).all()

    occupancy_data = []
    total_portions_all = 0
    occupied_portions_all = 0

    for building in buildings_query:
        # Count distinct portion numbers occupied in this building
        occupied_count = db.query(func.count(func.distinct(Tenant.portion_number))).filter(
            Tenant.building_id == building.building_id
        ).scalar() or 0

        total_portions = building.number_of_portions or 1
        total_portions_all += total_portions
        occupied_portions_all += min(occupied_count, total_portions)  # Can't exceed total

        occupancy_rate = (occupied_count / total_portions * 100) if total_portions > 0 else 0
        # Cap at 100%
        occupancy_rate = min(occupancy_rate, 100)

        occupancy_data.append({
            "building_id": building.building_id,
            "building_name": building.building_name,
            "total_portions": total_portions,
            "occupied_portions": occupied_count,
            "occupancy_rate": round(occupancy_rate, 2)
        })

    # Calculate overall vacancy stats for pie chart
    vacant_portions_all = total_portions_all - occupied_portions_all

    # Recent expiring tenants
    if filter_client_id:
        expiring_query = text("""
            SELECT
                t.tenant_id,
                t.name as tenant_name,
                b.building_name,
                t.agreement_end_date,
                DATEDIFF(t.agreement_end_date, CURDATE()) as days_remaining
            FROM tenants t
            LEFT JOIN buildings b ON t.building_id = b.building_id
            LEFT JOIN owners o ON t.owner_id = o.owner_id
            WHERE o.client_id = :client_id
              AND t.agreement_end_date >= :today
              AND t.agreement_end_date <= :expiry_date
            ORDER BY t.agreement_end_date
            LIMIT 10
        """)
        params = {"client_id": filter_client_id, "today": today, "expiry_date": expiry_date}
    else:
        expiring_query = text("""
            SELECT
                t.tenant_id,
                t.name as tenant_name,
                b.building_name,
                t.agreement_end_date,
                DATEDIFF(t.agreement_end_date, CURDATE()) as days_remaining
            FROM tenants t
            LEFT JOIN buildings b ON t.building_id = b.building_id
            WHERE t.agreement_end_date >= :today
              AND t.agreement_end_date <= :expiry_date
            ORDER BY t.agreement_end_date
            LIMIT 10
        """)
        params = {"today": today, "expiry_date": expiry_date}

    expiring_list = []
    with engine.connect() as connection:
        result_proxy = connection.execute(expiring_query, params)
        result_rows = result_proxy.mappings().fetchall()

        for row in result_rows:
            expiring_list.append({
                "tenant_id": row['tenant_id'],
                "tenant_name": row['tenant_name'],
                "building_name": row['building_name'] if row['building_name'] else "N/A",
                "agreement_end_date": row['agreement_end_date'].isoformat() if row['agreement_end_date'] else "",
                "days_remaining": row['days_remaining'] if row['days_remaining'] else 0
            })

    # Upcoming rent dues (tenants with rent due in next 7 days)
    current_day = today.day
    # Calculate days until due for each tenant
    if filter_client_id:
        rent_due_query = text("""
            SELECT
                t.tenant_id,
                t.name as tenant_name,
                t.phone,
                b.building_name,
                t.portion_number,
                t.rent_due_date,
                (t.rent_amount + t.water_charge + t.maintenance_charge) as total_rent,
                CASE
                    WHEN t.rent_due_date >= DAY(CURDATE()) THEN t.rent_due_date - DAY(CURDATE())
                    ELSE t.rent_due_date + (DAY(LAST_DAY(CURDATE())) - DAY(CURDATE()))
                END as days_until_due
            FROM tenants t
            LEFT JOIN buildings b ON t.building_id = b.building_id
            LEFT JOIN owners o ON t.owner_id = o.owner_id
            WHERE o.client_id = :client_id
              AND t.agreement_end_date >= :today
            HAVING days_until_due <= 7
            ORDER BY days_until_due
            LIMIT 10
        """)
        rent_due_params = {"client_id": filter_client_id, "today": today}
    else:
        rent_due_query = text("""
            SELECT
                t.tenant_id,
                t.name as tenant_name,
                t.phone,
                b.building_name,
                t.portion_number,
                t.rent_due_date,
                (t.rent_amount + t.water_charge + t.maintenance_charge) as total_rent,
                CASE
                    WHEN t.rent_due_date >= DAY(CURDATE()) THEN t.rent_due_date - DAY(CURDATE())
                    ELSE t.rent_due_date + (DAY(LAST_DAY(CURDATE())) - DAY(CURDATE()))
                END as days_until_due
            FROM tenants t
            LEFT JOIN buildings b ON t.building_id = b.building_id
            WHERE t.agreement_end_date >= :today
            HAVING days_until_due <= 7
            ORDER BY days_until_due
            LIMIT 10
        """)
        rent_due_params = {"today": today}

    rent_due_list = []
    with engine.connect() as connection:
        result_proxy = connection.execute(rent_due_query, rent_due_params)
        result_rows = result_proxy.mappings().fetchall()

        for row in result_rows:
            rent_due_list.append({
                "tenant_id": row['tenant_id'],
                "tenant_name": row['tenant_name'],
                "phone": row['phone'],
                "building_name": row['building_name'] if row['building_name'] else "N/A",
                "portion_number": row['portion_number'],
                "rent_due_date": row['rent_due_date'],
                "total_rent": float(row['total_rent']) if row['total_rent'] else 0,
                "days_until_due": row['days_until_due'] if row['days_until_due'] else 0
            })

    return {
        "total_owners": total_owners,
        "total_buildings": total_buildings,
        "total_tenants": total_tenants,
        "expiring_agreements": expiring_agreements,
        "building_occupancy": occupancy_data,
        "expiring_tenants": expiring_list,
        "upcoming_rent_dues": rent_due_list,
        # Overall occupancy for pie chart
        "total_portions": total_portions_all,
        "occupied_portions": occupied_portions_all,
        "vacant_portions": vacant_portions_all
    }
