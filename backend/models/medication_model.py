from pydantic import BaseModel
from typing import Optional, List, Literal
from datetime import datetime, time, date

# Medication frequency options
FrequencyType = Literal["DAILY", "SPECIFIC_DAYS", "INTERVAL", "AS_NEEDED"]

class MedicationSchedule(BaseModel):
    time: time
    frequency_type: FrequencyType
    days_of_week: Optional[List[str]] = None  # ["Monday", "Wednesday", "Friday"]
    interval_days: Optional[int] = None  # Every X days

class MedicationBase(BaseModel):
    user_id: str
    care_profile_id: Optional[str] = None
    name: str
    schedules: Optional[List[MedicationSchedule]] = None
    start_date: date
    end_date: Optional[date] = None
    prescribing_doctor: Optional[str] = None
    notes: Optional[str] = None
    inventory_count: Optional[int] = None
    refill_reminder_date: Optional[date] = None
    is_active: bool = True

# Create new medication
class MedicationCreate(MedicationBase):
    pass

# Update existing medication
class MedicationUpdate(BaseModel):
    name: Optional[str] = None
    schedules: Optional[List[MedicationSchedule]] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    prescribing_doctor: Optional[str] = None
    notes: Optional[str] = None
    inventory_count: Optional[int] = None
    refill_reminder_date: Optional[date] = None
    is_active: Optional[bool] = None

# Database representation with ID and timestamps
class MedicationInDB(MedicationBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Medication log models
class MedicationLogBase(BaseModel):
    medication_id: str
    care_profile_id: str
    timestamp: datetime
    quantity: Optional[str] = None
    notes: Optional[str] = None

# Create medication log entry
class MedicationLogCreate(MedicationLogBase):
    pass

# Database representation of medication log
class MedicationLogInDB(MedicationLogBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True