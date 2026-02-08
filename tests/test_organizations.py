import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.main import app
from app.models import Organization, Building, Activity, Phone
from app.config import settings
from sqlalchemy import select
from sqlalchemy.orm import selectinload

@pytest.mark.asyncio
async def test_get_organization_by_id(client, db_session):
    # Setup data
    b = Building(address="Test Addr", latitude=10.0, longitude=20.0)
    db_session.add(b)
    await db_session.commit()
    
    org = Organization(name="Target Org", building_id=b.id)
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    
    response = await client.get(f"/organizations/{org.id}", headers={"X-API-KEY": settings.STATIC_API_KEY})
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Target Org"
    assert data["building"]["address"] == "Test Addr"

@pytest.mark.asyncio
async def test_get_organization_not_found(client):
    response = await client.get("/organizations/9999", headers={"X-API-KEY": settings.STATIC_API_KEY})
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_search_organization_by_name(client, db_session):
    b = Building(address="Addr", latitude=0, longitude=0)
    db_session.add(b)
    await db_session.commit()
    
    org1 = Organization(name="Alpha Corp", building_id=b.id)
    org2 = Organization(name="Beta Ltd", building_id=b.id)
    org3 = Organization(name="Alpha & Omega", building_id=b.id)
    
    db_session.add_all([org1, org2, org3])
    await db_session.commit()
    
    response = await client.get("/organizations/search/name", params={"q": "Alpha"}, headers={"X-API-KEY": settings.STATIC_API_KEY})
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    names = [o["name"] for o in data]
    assert "Alpha Corp" in names
    assert "Alpha & Omega" in names
    assert "Beta Ltd" not in names

@pytest.mark.asyncio
async def test_get_organizations_by_building_id(client, db_session):
    b1 = Building(address="B1", latitude=0, longitude=0)
    b2 = Building(address="B2", latitude=1, longitude=1)
    db_session.add_all([b1, b2])
    await db_session.commit()
    
    org1 = Organization(name="Org in B1", building_id=b1.id)
    org2 = Organization(name="Org in B2", building_id=b2.id)
    db_session.add_all([org1, org2])
    await db_session.commit()
    
    # Test valid building with orgs
    response = await client.get(f"/organizations/building/{b1.id}", headers={"X-API-KEY": settings.STATIC_API_KEY})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Org in B1"
    
    # Test building with no orgs
    b3 = Building(address="Empty B3", latitude=2, longitude=2)
    db_session.add(b3)
    await db_session.commit()
    
    response = await client.get(f"/organizations/building/{b3.id}", headers={"X-API-KEY": settings.STATIC_API_KEY})
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_get_organizations_by_activity_tree(client, db_session):
    # Setup Activities
    # Root -> Child -> Grandchild
    root = Activity(name="Root")
    db_session.add(root)
    await db_session.commit()
    await db_session.refresh(root)
    
    child = Activity(name="Child", parent_id=root.id)
    db_session.add(child)
    await db_session.commit()
    await db_session.refresh(child)
    
    grandchild = Activity(name="Grandchild", parent_id=child.id)
    db_session.add(grandchild)
    await db_session.commit()
    await db_session.refresh(grandchild)
    
    other_root = Activity(name="Other")
    db_session.add(other_root)
    await db_session.commit()
    await db_session.refresh(other_root)
    
    # Setup Building & Orgs
    b = Building(address="B", latitude=0, longitude=0)
    db_session.add(b)
    await db_session.commit()
    
    # Org with Root
    org1 = Organization(name="Root Org", building_id=b.id)
    db_session.add(org1)
    await db_session.commit()
    # Eager load to avoid MissingGreenlet
    stmt = select(Organization).options(selectinload(Organization.activities)).where(Organization.id == org1.id)
    result = await db_session.execute(stmt)
    org1 = result.scalars().first()
    org1.activities.append(root)
    
    # Org with Grandchild
    org2 = Organization(name="Deep Org", building_id=b.id)
    db_session.add(org2)
    await db_session.commit()
    stmt = select(Organization).options(selectinload(Organization.activities)).where(Organization.id == org2.id)
    result = await db_session.execute(stmt)
    org2 = result.scalars().first()
    org2.activities.append(grandchild)
    
    # Org with Other
    org3 = Organization(name="Other Org", building_id=b.id)
    db_session.add(org3)
    await db_session.commit()
    stmt = select(Organization).options(selectinload(Organization.activities)).where(Organization.id == org3.id)
    result = await db_session.execute(stmt)
    org3 = result.scalars().first()
    org3.activities.append(other_root)
    
    await db_session.commit()
    
    # Test searching by Root (should find Org1 and Org2)
    response = await client.get(f"/organizations/activity/{root.id}", headers={"X-API-KEY": settings.STATIC_API_KEY})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    names = [o["name"] for o in data]
    assert "Root Org" in names
    assert "Deep Org" in names
    assert "Other Org" not in names
    
    # Test searching by Child (should find Org2)
    # Wait, Org1 is linked to Root. Does searching by Child find Org1? NO. Child is below Root.
    # Searching by Child finds things linked to Child or Grandchild.
    response = await client.get(f"/organizations/activity/{child.id}", headers={"X-API-KEY": settings.STATIC_API_KEY})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Deep Org"
    
    # Test searching by Grandchild (should find Org2)
    response = await client.get(f"/organizations/activity/{grandchild.id}", headers={"X-API-KEY": settings.STATIC_API_KEY})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Deep Org"

@pytest.mark.asyncio
async def test_geo_search(client, db_session):
    # Setup: 3 buildings.
    # B1: (0, 0) - Center
    # B2: (0, 0.1) - Close (~11km)
    # B3: (10, 10) - Far (>1000km)
    
    b1 = Building(address="Center", latitude=0.0, longitude=0.0)
    b2 = Building(address="Close", latitude=0.0, longitude=0.1) 
    b3 = Building(address="Far", latitude=10.0, longitude=10.0)
    
    db_session.add_all([b1, b2, b3])
    await db_session.commit()
    
    org1 = Organization(name="Org1", building_id=b1.id)
    org2 = Organization(name="Org2", building_id=b2.id)
    org3 = Organization(name="Org3", building_id=b3.id)
    
    db_session.add_all([org1, org2, org3])
    await db_session.commit()
    
    # Test Radius
    # Search near (0,0) with radius 20km. Should find B1 and B2.
    # 0.1 deg lon at equator is ~11.1km.
    response = await client.get("/organizations/building/radius", params={"lat": 0, "lon": 0, "radius_km": 15}, headers={"X-API-KEY": settings.STATIC_API_KEY})
    assert response.status_code == 200
    data = response.json()
    names = [o["name"] for o in data]
    assert "Org1" in names
    assert "Org2" in names
    assert "Org3" not in names
    
    # Test BBox
    # Box covering (0,0) to (1,1). Should find B1 and B2 (if 0.1 < 1).
    response = await client.get("/organizations/building/bbox", params={"min_lat": -1, "min_lon": -1, "max_lat": 1, "max_lon": 1}, headers={"X-API-KEY": settings.STATIC_API_KEY})
    assert response.status_code == 200
    data = response.json()
    names = [o["name"] for o in data]
    assert "Org1" in names
    assert "Org2" in names
    assert "Org3" not in names

@pytest.mark.asyncio
async def test_get_buildings_list(client: AsyncClient, db_session: AsyncSession):
    # Ensure buildings exist
    b1 = Building(address="ListB1", latitude=10, longitude=10)
    b2 = Building(address="ListB2", latitude=20, longitude=20)
    db_session.add_all([b1, b2])
    await db_session.commit()
    
    response = await client.get("/organizations/buildings/list", headers={"X-API-KEY": settings.STATIC_API_KEY})
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    addresses = [b['address'] for b in data]
    assert "ListB1" in addresses
    assert "ListB2" in addresses
