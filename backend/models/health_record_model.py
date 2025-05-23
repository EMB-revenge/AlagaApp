from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal, Union
from datetime import datetime
from enum import Enum

# Define RecordType Enum
class RecordType(str, Enum):
    BLOOD_PRESSURE = "blood_pressure"
    GLUCOSE_LEVEL = "glucose_level"
    HEART_RATE = "heart_rate"
    TEMPERATURE = "temperature"
    WEIGHT = "weight"
    HEIGHT = "height"
    BMI = "bmi"
    OXYGEN_SATURATION = "oxygen_saturation"
    # Add other vital sign types as needed
    ALLERGY = "allergy" # Example non-vital health record type
    VACCINATION = "vaccination" # Example non-vital health record type
    LAB_RESULT = "lab_result" # Example non-vital health record type

# Define specific value models for structured data like Blood Pressure
class BloodPressureValue(BaseModel):
    systolic: int # mmHg
    diastolic: int # mmHg
    # Optional: heart_rate: Optional[int] = None # BPM, often measured with BP

class HealthRecordBase(BaseModel):
    user_id: str
    care_profile_id: Optional[str] = None
    record_type: RecordType # Use RecordType Enum
    date_recorded: datetime
    value: Union[Dict[str, Any], BloodPressureValue, int, float, str] # Use Union for flexible value types, including specific models
    unit: Optional[str] = None # e.g., 'mmHg', 'mg/dL', 'kg'
    notes: Optional[str] = None
    source: Optional[str] = None # e.g., 'manual_entry', 'wearable_device', 'clinic_import'
    document_url: Optional[str] = None # For attaching files like lab reports

class HealthRecordCreate(HealthRecordBase):
    pass

class HealthRecordUpdate(BaseModel):
    record_type: Optional[RecordType] = None # Use RecordType Enum
    date_recorded: Optional[datetime] = None
    value: Optional[Union[Dict[str, Any], BloodPressureValue, int, float, str]] = None # Use Union
    unit: Optional[str] = None
    notes: Optional[str] = None
    source: Optional[str] = None
    document_url: Optional[str] = None

class HealthRecordInDB(HealthRecordBase):
    id: str # Document ID from Firestore
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }