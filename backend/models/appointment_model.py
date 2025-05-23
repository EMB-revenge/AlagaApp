from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime, date, time
from enum import Enum

# Define Enums for Appointment Type and Status
class AppointmentType(str, Enum):
    CHECK_UP = "check-up"
    SPECIALIST = "specialist"
    TELEHEALTH = "telehealth"
    OTHER = "other"

class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"

class AppointmentBase(BaseModel):
    user_id: str
    care_profile_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    appointment_time: datetime
    duration_minutes: Optional[int] = None
    location: Optional[str] = None
    doctor_name: Optional[str] = None
    appointment_type: Optional[AppointmentType] = None # Use Enum
    status: AppointmentStatus = AppointmentStatus.SCHEDULED # Use Enum with default
    notes: Optional[str] = None
    reminder_sent: bool = False # Consider this a flag for logic, not necessarily database storage

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    appointment_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    location: Optional[str] = None
    doctor_name: Optional[str] = None
    appointment_type: Optional[AppointmentType] = None # Use Enum
    status: Optional[AppointmentStatus] = None # Use Enum
    notes: Optional[str] = None
    reminder_sent: Optional[bool] = None

class AppointmentInDB(AppointmentBase):
    id: str # Document ID from Firestore
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }