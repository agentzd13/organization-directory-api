from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import List, Optional

class PhoneBase(BaseModel):
    number: str = Field(..., description="Phone number string", example="8-800-555-35-35")

class PhoneCreate(PhoneBase):
    pass

class Phone(PhoneBase):
    id: int = Field(..., description="Unique ID of the phone")
    organization_id: int = Field(..., description="ID of the related organization")

    model_config = ConfigDict(from_attributes=True)

class BuildingBase(BaseModel):
    address: str = Field(..., description="Physical address of the building", example="Moscow, Lenin St, 1")
    latitude: float = Field(..., description="Latitude coordinate (-90 to 90)", example=55.7558)
    longitude: float = Field(..., description="Longitude coordinate (-180 to 180)", example=37.6173)

    @field_validator('latitude')
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        if not (-90 <= v <= 90):
            raise ValueError('Latitude must be between -90 and 90')
        return v

    @field_validator('longitude')
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        if not (-180 <= v <= 180):
            raise ValueError('Longitude must be between -180 and 180')
        return v

class BuildingCreate(BuildingBase):
    pass

class Building(BuildingBase):
    id: int = Field(..., description="Unique ID of the building")
    
    model_config = ConfigDict(from_attributes=True)

class ActivityBase(BaseModel):
    name: str = Field(..., description="Name of the activity", example="Food")

class ActivityCreate(ActivityBase):
    parent_id: Optional[int] = Field(None, description="ID of the parent activity (if any)")

class Activity(ActivityBase):
    id: int = Field(..., description="Unique ID of the activity")
    parent_id: Optional[int] = Field(None, description="ID of the parent activity")
    children: List['Activity'] = Field([], description="List of child activities (recursive)")

    model_config = ConfigDict(from_attributes=True)

class ActivityFlat(ActivityBase):
    id: int = Field(..., description="Unique ID of the activity")
    parent_id: Optional[int] = Field(None, description="ID of the parent activity")
    
    model_config = ConfigDict(from_attributes=True)

class OrganizationBase(BaseModel):
    name: str = Field(..., description="Name of the organization", example="OOO Horns and Hooves")
    building_id: int = Field(..., description="ID of the building location")
    activity_ids: List[int] = Field([], description="List of activity IDs associated with the organization")

class OrganizationCreate(OrganizationBase):
    phones: List[str] = Field([], description="List of phone numbers", example=["8-800-555-35-35"])

class Organization(BaseModel):
    id: int = Field(..., description="Unique ID of the organization")
    name: str = Field(..., description="Name of the organization")
    building: Building = Field(..., description="Building details")
    activities: List[ActivityFlat] = Field(..., description="List of activities (flat structure)")
    phones: List[Phone] = Field(..., description="List of phone numbers")

    model_config = ConfigDict(from_attributes=True)
