from pydantic import BaseModel, Field
from typing import Optional, List

class CareProfileBase(BaseModel):
    """Base model for care profiles - represents a person being cared for"""
    full_name: str
    relationship: str  # e.g., "parent", "grandparent", "sibling", etc.
    condition: Optional[str] = None  # Primary health condition if any
    birth_date: Optional[str] = None
    gender: Optional[str] = None
    blood_type: Optional[str] = None
    allergies: Optional[List[str]] = None
    emergency_contact: Optional[str] = None
    notes: Optional[str] = None
    profile_picture_url: Optional[str] = None

class CareProfileCreate(CareProfileBase):
    """Model for creating a new care profile"""
    pass

class CareProfileUpdate(BaseModel):
    """Model for updating an existing care profile"""
    full_name: Optional[str] = None
    relationship: Optional[str] = None
    condition: Optional[str] = None
    birth_date: Optional[str] = None
    gender: Optional[str] = None
    blood_type: Optional[str] = None
    allergies: Optional[List[str]] = None
    emergency_contact: Optional[str] = None
    notes: Optional[str] = None
    profile_picture_url: Optional[str] = None

class CareProfileInDB(CareProfileBase):
    """Model for a care profile as stored in the database"""
    id: str
    user_id: str  # ID of the caregiver who created this profile
    created_at: str
    updated_at: str