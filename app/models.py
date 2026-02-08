from sqlalchemy import Column, Integer, String, Float, ForeignKey, Table, event
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .database import Base

# Association table for Organization <-> Activity
organization_activities = Table(
    "organization_activities",
    Base.metadata,
    Column("organization_id", ForeignKey("organizations.id"), primary_key=True),
    Column("activity_id", ForeignKey("activities.id"), primary_key=True),
)

class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("activities.id"), nullable=True)

    # Self-referencing relationship
    children = relationship("Activity", back_populates="parent", cascade="all, delete-orphan")
    parent = relationship("Activity", back_populates="children", remote_side=[id])

    organizations = relationship("Organization", secondary=organization_activities, back_populates="activities")

    def __repr__(self):
        return f"<Activity(id={self.id}, name='{self.name}', parent_id={self.parent_id})>"

class Building(Base):
    __tablename__ = "buildings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    address: Mapped[str] = mapped_column(String)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)

    organizations = relationship("Organization", back_populates="building")

    def __repr__(self):
        return f"<Building(id={self.id}, address='{self.address}')>"

class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    building_id: Mapped[int] = mapped_column(ForeignKey("buildings.id"), nullable=False)

    building = relationship("Building", back_populates="organizations")
    activities = relationship("Activity", secondary=organization_activities, back_populates="organizations")
    phones = relationship("Phone", back_populates="organization", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Organization(id={self.id}, name='{self.name}')>"

class Phone(Base):
    __tablename__ = "phones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    number: Mapped[str] = mapped_column(String)

    organization = relationship("Organization", back_populates="phones")

    def __repr__(self):
        return f"<Phone(id={self.id}, number='{self.number}')>"

# --- Validation Logic for Activity Depth ---

from sqlalchemy import inspect

# Logic moved to Database Triggers for robust enforcement
# See migration versions/xxxx_add_depth_check_trigger.py

# We also attach DDL listeners here so that tests (which use metadata.create_all)
# get the triggers without running alembic.
from sqlalchemy import DDL

trigger_insert_ddl = DDL("""
CREATE TRIGGER check_depth_insert 
BEFORE INSERT ON activities 
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Max activity tree depth (3) exceeded')
    WHERE (
        WITH RECURSIVE parent_chain(id, parent_id, level) AS (
            SELECT id, parent_id, 1 FROM activities WHERE id = NEW.parent_id
            UNION ALL
            SELECT a.id, a.parent_id, pc.level + 1
            FROM activities a JOIN parent_chain pc ON a.id = pc.parent_id
        )
        SELECT MAX(level) FROM parent_chain
    ) >= 3;
END;
""")

trigger_update_ddl = DDL("""
CREATE TRIGGER check_depth_update
BEFORE UPDATE OF parent_id ON activities 
FOR EACH ROW
WHEN NEW.parent_id IS NOT NULL
BEGIN
    SELECT RAISE(ABORT, 'Max activity tree depth (3) exceeded')
    WHERE (
        WITH RECURSIVE parent_chain(id, parent_id, level) AS (
            SELECT id, parent_id, 1 FROM activities WHERE id = NEW.parent_id
            UNION ALL
            SELECT a.id, a.parent_id, pc.level + 1
            FROM activities a JOIN parent_chain pc ON a.id = pc.parent_id
        )
        SELECT MAX(level) FROM parent_chain
    ) >= 3;
END;
""")

event.listen(Activity.__table__, 'after_create', trigger_insert_ddl)
event.listen(Activity.__table__, 'after_create', trigger_update_ddl)
