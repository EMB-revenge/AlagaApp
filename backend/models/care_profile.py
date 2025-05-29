from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime, date
from enum import Enum

class CareProfileBase(BaseModel):
    """Base model for care profile data (person being cared for)"""
    full_name: str
    relationship: str  # Relationship to the caregiver
    condition: Optional[str] = None  # Primary health condition
    birth_date: Optional[date] = None # Date of birth
    gender: Optional[str] = None # Gender identity
    blood_type: Optional[str] = None # Blood type
    allergies: Optional[List[str]] = None
    emergency_contact: Optional[str] = None
    notes: Optional[str] = None
    profile_picture_url: Optional[str] = None

# Model for creating a new care profile, inherits from CareProfileBase
class CareProfileCreate(CareProfileBase):
    user_id: str  # ID of the user (caregiver) creating this profile

# Model for updating an existing care profile, all fields are optional
class CareProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    relationship: Optional[str] = None
    condition: Optional[str] = None
    birth_date: Optional[date] = None
    gender: Optional[str] = None
    blood_type: Optional[str] = None
    allergies: Optional[List[str]] = None
    emergency_contact: Optional[str] = None
    notes: Optional[str] = None
    profile_picture_url: Optional[str] = None

# Model representing a care profile in the database, includes ID and timestamps
class CareProfileInDB(CareProfileBase):
    id: str
    user_id: str  # ID of the user (caregiver) who created this profile
    created_at: datetime # Timestamp of creation
    updated_at: datetime # Timestamp of last update

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat(), # Custom encoder for datetime objects
            date: lambda d: d.isoformat() # Custom encoder for date objects
        }