from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime, time, date

# Define FrequencyType Enum-like using Literal for clarity and validation
# Based on usage in backend/routers/medications.py
FrequencyType = Literal["DAILY", "SPECIFIC_DAYS", "INTERVAL", "AS_NEEDED"] # Added AS_NEEDED based on potential frequency options

class MedicationSchedule(BaseModel):
    time: time # Time of day for the dosage
    frequency_type: FrequencyType
    days_of_week: Optional[List[str]] = None # e.g., ["Monday", "Wednesday", "Friday"]
    interval_days: Optional[int] = None # e.g., 2 (for every 2 days)
    # Consider adding quantity and instruction here if dosage varies by schedule

class Dosage(BaseModel):
    time: time # Time of day for the dosage
    quantity: str # e.g., "1 pill", "10ml"
    instruction: Optional[str] = None
    # instruction: Optional[str] = None # e.g., "with food", "before bedtime"

class MedicationBase(BaseModel):
    user_id: str
    care_profile_id: Optional[str] = None
    name: str
    # Removed simplified dosage and frequency fields, replaced by schedules
    # dosage: str # Simplified dosage instruction, e.g., "1 pill twice a day"
    # frequency: Optional[str] = None # e.g., "daily", "as_needed"
    schedules: Optional[List[MedicationSchedule]] = None # Use the structured schedule model
    start_date: date # Changed to date type
    end_date: Optional[date] = None # Changed to date type
    prescribing_doctor: Optional[str] = None
    notes: Optional[str] = None
    inventory_count: Optional[int] = None
    refill_reminder_date: Optional[date] = None # Changed to date type
    is_active: bool = True

class MedicationCreate(MedicationBase):
    pass
    # If dosage quantity/instruction is per schedule, might need adjustment here

class MedicationUpdate(BaseModel):
    name: Optional[str] = None
    # Removed simplified dosage and frequency fields
    # dosage: Optional[str] = None
    # frequency: Optional[str] = None
    schedules: Optional[List[MedicationSchedule]] = None # Use the structured schedule model
    start_date: Optional[date] = None # Changed to date type
    end_date: Optional[date] = None # Changed to date type
    prescribing_doctor: Optional[str] = None
    notes: Optional[str] = None
    inventory_count: Optional[int] = None
    refill_reminder_date: Optional[date] = None # Changed to date type
    is_active: Optional[bool] = None
    # If dosage quantity/instruction is per schedule, might need adjustment here

class MedicationInDB(MedicationBase):
    id: str # Document ID from Firestore
    created_at: datetime
    updated_at: datetime
    # If Dosage model with quantity/instruction per schedule is used, update this too

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            time: lambda t: t.isoformat(),
            date: lambda d: d.isoformat() # Add encoder for date type
        }