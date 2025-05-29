from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime, date, time
from enum import Enum

# Enum for different types of appointments
class AppointmentType(str, Enum):
    CHECK_UP = "check-up"
    SPECIALIST = "specialist"
    TELEHEALTH = "telehealth"
    OTHER = "other"

# Enum for the status of an appointment
class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"

# Base model for appointment data
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
    status: AppointmentStatus = AppointmentStatus.SCHEDULED # Default status for new appointments
    notes: Optional[str] = None
    reminder_sent: bool = False # Flag to track if a reminder has been sent

# Model for creating a new appointment, inherits from AppointmentBase
class AppointmentCreate(AppointmentBase):
    pass

# Model for updating an existing appointment, all fields are optional
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

# Model representing an appointment as stored in the database, includes ID and timestamps
class AppointmentInDB(AppointmentBase):
    id: str # Firestore document ID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        allow_population_by_field_name = True # Allows populating model by field name (e.g. for '_id' from DB)
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }