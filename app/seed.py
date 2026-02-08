import asyncio
import sys
import os

# Ensure app is in path
sys.path.append(os.getcwd())

from sqlalchemy import delete
from app.database import SessionLocal, engine, Base
from app.models import Organization, Building, Activity, Phone, organization_activities

async def seed_data():
    async with SessionLocal() as session:
        print("Cleaning up old data...")
        # Order matters for foreign keys
        await session.execute(delete(Phone))
        await session.execute(delete(organization_activities))
        await session.execute(delete(Organization))
        await session.execute(delete(Building))
        await session.execute(delete(Activity))
        await session.commit()
        
        print("Creating Buildings...")
        b1 = Building(address="Moscow, Lenina 1", latitude=55.7558, longitude=37.6173)
        b2 = Building(address="Moscow, Tverskaya 12", latitude=55.7600, longitude=37.6000)
        b3 = Building(address="Saint Petersburg, Nevsky 20", latitude=59.9343, longitude=30.3351)
        session.add_all([b1, b2, b3])
        await session.commit()
        # Refresh to get IDs
        await session.refresh(b1)
        await session.refresh(b2)
        await session.refresh(b3)

        print("Creating Activities (Tree)...")
        # Level 1
        food = Activity(name="Food")
        cars = Activity(name="Automotive")
        it = Activity(name="IT Services")
        session.add_all([food, cars, it])
        await session.commit()
        await session.refresh(food)
        await session.refresh(cars)
        
        # Level 2
        meat = Activity(name="Meat Products", parent_id=food.id)
        dairy = Activity(name="Dairy Products", parent_id=food.id)
        spare_parts = Activity(name="Spare Parts", parent_id=cars.id)
        session.add_all([meat, dairy, spare_parts])
        await session.commit()
        await session.refresh(meat)
        await session.refresh(spare_parts)
        
        # Level 3
        sausages = Activity(name="Sausages", parent_id=meat.id)
        tires = Activity(name="Tires", parent_id=spare_parts.id)
        session.add_all([sausages, tires])
        await session.commit()
        
        print("Creating Organizations...")
        # Org 1: Food > Meat > Sausages, located at b1
        org1 = Organization(name="Sausage King", building_id=b1.id, activities=[sausages, meat])
        session.add(org1)
        
        # Org 2: Automotive > Parts, located at b2
        org2 = Organization(name="AutoFix", building_id=b2.id, activities=[spare_parts, tires])
        session.add(org2)

        # Org 3: IT, located at b3
        org3 = Organization(name="SoftDev", building_id=b3.id, activities=[it])
        session.add(org3)
        
        await session.commit()
        await session.refresh(org1)
        await session.refresh(org3)

        print("Creating Phones...")
        p1 = Phone(number="8-800-555-35-35", organization_id=org1.id)
        p2 = Phone(number="8-495-123-45-67", organization_id=org1.id)
        p3 = Phone(number="8-812-987-65-43", organization_id=org3.id)
        session.add_all([p1, p2, p3])
        await session.commit()
        
        print("Data seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed_data())
