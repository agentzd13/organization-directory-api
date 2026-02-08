import asyncio
import sys
import os

sys.path.append(os.getcwd())

from sqlalchemy import select, func
from app.database import SessionLocal
from app.models import Organization, Building, Activity, Phone

async def verify_data():
    async with SessionLocal() as session:
        b_count = await session.scalar(select(func.count()).select_from(Building))
        a_count = await session.scalar(select(func.count()).select_from(Activity))
        o_count = await session.scalar(select(func.count()).select_from(Organization))
        p_count = await session.scalar(select(func.count()).select_from(Phone))
        
        print(f"Buildings: {b_count}")
        print(f"Activities: {a_count}")
        print(f"Organizations: {o_count}")
        print(f"Phones: {p_count}")
        
        if b_count >= 3 and a_count >= 8 and o_count >= 3 and p_count >= 3:
            print("Data verification passed!")
        else:
            print("Data verification FAILED.")

if __name__ == "__main__":
    asyncio.run(verify_data())
