import pytest
from app.models import Activity
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

@pytest.mark.asyncio
async def test_create_depth_exceeding_activity(db_session: AsyncSession):
    # Level 1
    root = Activity(name="Root")
    db_session.add(root)
    await db_session.commit()
    await db_session.refresh(root)
    
    # Level 2
    l2 = Activity(name="L2", parent_id=root.id)
    db_session.add(l2)
    await db_session.commit()
    await db_session.refresh(l2)
    
    # Level 3
    l3 = Activity(name="L3", parent_id=l2.id)
    db_session.add(l3)
    await db_session.commit()
    await db_session.refresh(l3)
    
    # Level 4 - Should FAIL
    l4 = Activity(name="L4", parent_id=l3.id)
    db_session.add(l4)
    
    try:
        await db_session.commit()
        pytest.fail("Managed to create Activity with depth 4! Constraint missing.")
    except Exception as e:
        # We expect a database error here (OperationalError or similar from sqlite)
        assert "Max activity tree depth" in str(e) or "constraint failed" in str(e) or "ABORT" in str(e)
        # Rollback is needed after error
        await db_session.rollback()
