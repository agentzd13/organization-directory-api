from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List

from app.database import get_db
from app.models import Organization
from app.schemas import Organization as OrganizationSchema, Building

router = APIRouter(prefix="/organizations", tags=["organizations"])

@router.get("/search/name", response_model=List[OrganizationSchema], summary="Search Organizations by Name", description="Find organizations whose name matches the query string (case-insensitive partial match).")
async def search_organizations_by_name(
    q: str = Query(..., min_length=1, description="Partial name to search for"),
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(Organization)
        .options(
            selectinload(Organization.building),
            selectinload(Organization.activities),
            selectinload(Organization.phones)
        )
        .where(Organization.name.ilike(f"%{q}%"))
    )
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{org_id}", response_model=OrganizationSchema, summary="Get Organization by ID", description="Retrieve detailed information about a specific organization, including its building, activities, and phone numbers.")
async def get_organization_by_id(
    org_id: int,
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(Organization)
        .options(
            selectinload(Organization.building),
            selectinload(Organization.activities),
            selectinload(Organization.phones)
        )
        .where(Organization.id == org_id)
    )
    result = await db.execute(query)
    org = result.scalars().first()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    return org

@router.get("/building/radius", response_model=List[OrganizationSchema], summary="Search Organizations by Radius", description="Find organizations within a specified distance (in km) from a geographic point.")
async def get_organizations_by_radius(
    lat: float,
    lon: float,
    radius_km: float,
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(Organization)
        .join(Organization.building)
        .options(
            selectinload(Organization.building),
            selectinload(Organization.activities),
            selectinload(Organization.phones)
        )
    )
    result = await db.execute(query)
    all_orgs = result.scalars().all()
    
    import math
    
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371  # km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2) * math.sin(dlat / 2) + \
            math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
            math.sin(dlon / 2) * math.sin(dlon / 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c
        
    filtered_orgs = []
    for org in all_orgs:
        dist = haversine(lat, lon, org.building.latitude, org.building.longitude)
        if dist <= radius_km:
            filtered_orgs.append(org)
            
    return filtered_orgs

@router.get("/building/bbox", response_model=List[OrganizationSchema], summary="Search Organizations by Bounding Box", description="Find organizations located within a rectangular geographic area defined by min/max latitude and longitude.")
async def get_organizations_by_bbox(
    min_lat: float,
    min_lon: float,
    max_lat: float,
    max_lon: float,
    db: AsyncSession = Depends(get_db)
):
    from app.models import Building
    query = (
        select(Organization)
        .join(Organization.building)
        .options(
            selectinload(Organization.building),
            selectinload(Organization.activities),
            selectinload(Organization.phones)
        )
        .where(
            Building.latitude >= min_lat,
            Building.latitude <= max_lat,
            Building.longitude >= min_lon,
            Building.longitude <= max_lon
        )
    )
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/building/{building_id}", response_model=List[OrganizationSchema], summary="Get Organizations by Building", description="List all organizations located in a specific building.")
async def get_organizations_by_building_id(
    building_id: int,
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(Organization)
        .options(
            selectinload(Organization.building),
            selectinload(Organization.activities),
            selectinload(Organization.phones)
        )
        .where(Organization.building_id == building_id)
    )
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/activity/{activity_id}", response_model=List[OrganizationSchema], summary="Get Organizations by Activity (Tree Search)", description="Find organizations associated with a specific activity or any of its sub-categories (up to 3 levels deep).")
async def get_organizations_by_activity_id(
    activity_id: int,
    db: AsyncSession = Depends(get_db)
):
    related_ids = {activity_id}
    
    # Get all activities to traverse in memory (dataset is small)
    # Alternatively, iterative query
    # Let's do iterative for depth 3
    from app.models import Activity
    
    current_ids = [activity_id]
    
    for _ in range(3): # Max depth 3
        if not current_ids:
            break
        stmt = select(Activity.id).where(Activity.parent_id.in_(current_ids))
        result = await db.execute(stmt)
        children = result.scalars().all()
        current_ids = children
        related_ids.update(children)
        
    query = (
        select(Organization)
        .join(Organization.activities)
        .options(
            selectinload(Organization.building),
            selectinload(Organization.activities),
            selectinload(Organization.phones)
        )
        .where(Organization.activities.any(Activity.id.in_(related_ids)))
        .distinct()
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/buildings/list", response_model=List[Building], summary="List All Buildings", description="Retrieve a list of all buildings in the directory.")
async def get_buildings(
    db: AsyncSession = Depends(get_db)
):
    from app.models import Building
    # from app.schemas import Building as BuildingSchema # Validation via response_model
    query = select(Building)
    result = await db.execute(query)
    return result.scalars().all()


