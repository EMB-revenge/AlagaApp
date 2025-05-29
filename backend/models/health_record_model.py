from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal, Union
from datetime import datetime
from enum import Enum

# Enum for different types of health records
class RecordType(str, Enum):
    BLOOD_PRESSURE = "blood_pressure"
    GLUCOSE_LEVEL = "glucose_level"
    HEART_RATE = "heart_rate"
    TEMPERATURE = "temperature"
    WEIGHT = "weight"
    HEIGHT = "height"
    BMI = "bmi"
    OXYGEN_SATURATION = "oxygen_saturation"
    # Other non-vital health record types
    ALLERGY = "allergy"
    VACCINATION = "vaccination"
    LAB_RESULT = "lab_result"

# Model for structured blood pressure readings
class BloodPressureValue(BaseModel):
    systolic: int # Systolic pressure in mmHg
    diastolic: int # Diastolic pressure in mmHg
    # heart_rate: Optional[int] = None # Optional: heart rate in BPM

# Base model for health record data
class HealthRecordBase(BaseModel):
    user_id: str
    care_profile_id: Optional[str] = None
    record_type: RecordType # Type of health record
    date_recorded: datetime # Timestamp when the record was made
    value: Union[Dict[str, Any], BloodPressureValue, int, float, str] # Actual value of the record, can be various types
    unit: Optional[str] = None # Unit of measurement (e.g., 'mmHg', 'mg/dL')
    notes: Optional[str] = None # Additional notes about the record
    source: Optional[str] = None # Source of the data (e.g., 'manual_entry', 'wearable_device')
    document_url: Optional[str] = None # URL to an attached document (e.g., lab report PDF)

# Model for creating a new health record, inherits from HealthRecordBase
class HealthRecordCreate(HealthRecordBase):
    pass

# Model for updating an existing health record, all fields are optional
class HealthRecordUpdate(BaseModel):
    record_type: Optional[RecordType] = None
    date_recorded: Optional[datetime] = None
    value: Optional[Union[Dict[str, Any], BloodPressureValue, int, float, str]] = None
    unit: Optional[str] = None
    notes: Optional[str] = None
    source: Optional[str] = None
    document_url: Optional[str] = None

# Model representing a health record in the database, includes ID and timestamps
class HealthRecordInDB(HealthRecordBase):
    id: str # Firestore document ID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat() # Custom encoder for datetime objects
        }