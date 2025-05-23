from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime, date
from enum import Enum

# Optional: Define Enums for relationship, gender, blood type if using fixed values
# class RelationshipType(str, Enum):
#     PARENT = "parent"
#     GRANDPARENT = "grandparent"
#     SIBLING = "sibling"
#     OTHER = "other"

# class Gender(str, Enum):
#     MALE = "Male"
#     FEMALE = "Female"
#     OTHER = "Other"
#     PREFER_NOT_TO_SAY = "Prefer not to say"

# class BloodType(str, Enum):
#     A_POS = "A+"
#     A_NEG = "A-"
#     B_POS = "B+"
#     B_NEG = "B-"
#     AB_POS = "AB+"
#     AB_NEG = "AB-"
#     O_POS = "O+"
#     O_NEG = "O-"

class CareProfileBase(BaseModel):
    """Base model for care profiles - represents a person being cared for"""
    full_name: str
    relationship: str  # Or use RelationshipType Enum
    condition: Optional[str] = None  # Primary health condition if any
    birth_date: Optional[date] = None # Changed to date type
    gender: Optional[str] = None # Or use Gender Enum
    blood_type: Optional[str] = None # Or use BloodType Enum
    allergies: Optional[List[str]] = None
    emergency_contact: Optional[str] = None
    notes: Optional[str] = None
    profile_picture_url: Optional[str] = None

class CareProfileCreate(CareProfileBase):
    """Model for creating a new care profile"""
    user_id: str  # ID of the caregiver creating this profile

class CareProfileUpdate(BaseModel):
    """Model for updating an existing care profile"""
    full_name: Optional[str] = None
    relationship: Optional[str] = None # Or use RelationshipType Enum
    condition: Optional[str] = None
    birth_date: Optional[date] = None # Changed to date type
    gender: Optional[str] = None # Or use Gender Enum
    blood_type: Optional[str] = None # Or use BloodType Enum
    allergies: Optional[List[str]] = None
    emergency_contact: Optional[str] = None
    notes: Optional[str] = None
    profile_picture_url: Optional[str] = None

class CareProfileInDB(CareProfileBase):
    """Model for a care profile as stored in the database"""
    id: str
    user_id: str  # ID of the caregiver who created this profile
    created_at: datetime # Changed to datetime type
    updated_at: datetime # Changed to datetime type

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            date: lambda d: d.isoformat() # Add encoder for date type
        }