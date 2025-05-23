from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    phone_number: Optional[str] = None
    birth_date: Optional[str] = None # Consider using date type after validation
    gender: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None

class UserCreate(UserBase):
    password: str # Password will be hashed before saving

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    birth_date: Optional[str] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    profile_picture_url: Optional[str] = None
    is_caregiver: Optional[bool] = None
    # is_verified is typically handled by system, not direct user update

class UserInDB(UserBase):
    id: str # Document ID from Firestore
    created_at: datetime
    updated_at: datetime
    profile_picture_url: Optional[str] = None
    is_caregiver: bool = False
    is_verified: bool = False # e.g., email verification status

    class Config:
        orm_mode = True
        allow_population_by_field_name = True # Ensures 'id' can be populated even if input data has '_id'
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }