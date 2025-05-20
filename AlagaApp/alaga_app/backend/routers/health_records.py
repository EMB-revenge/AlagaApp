from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from firebase_admin import firestore
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

router = APIRouter(
    prefix="/health-records",
    tags=["health_records"],
)

# Use globally initialized Firestore client
from ..main import db

# Models
class HealthMetric(BaseModel):
    metric_type: str  # e.g., "blood_pressure", "blood_sugar", "weight", etc.
    value: str
    unit: str
    timestamp: Optional[str] = None
    notes: Optional[str] = None

class HealthCondition(BaseModel):
    name: str
    diagnosed_date: Optional[str] = None
    status: Optional[str] = None  # e.g., "active", "managed", "resolved"
    notes: Optional[str] = None

class HealthRecordBase(BaseModel):
    user_id: str
    patient_id: str  # ID of the person being cared for
    record_type: str  # e.g., "vital", "condition", "note", etc.
    data: dict  # Flexible schema to store different types of health data

class HealthRecordCreate(BaseModel):
    patient_id: str
    record_type: str
    data: dict

class HealthRecordUpdate(BaseModel):
    record_type: Optional[str] = None
    data: Optional[dict] = None

class HealthRecordInDB(HealthRecordBase):
    id: str
    created_at: str
    updated_at: str

# Helper functions
def get_health_record_by_id(record_id: str):
    try:
        record_doc = db.collection('health_records').document(record_id).get()
        if record_doc.exists:
            return record_doc.to_dict()
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Routes
@router.post("/", response_model=HealthRecordInDB, status_code=status.HTTP_201_CREATED)
async def create_health_record(record: HealthRecordCreate, user_id: str):
    try:
        # Create health record in Firestore
        current_time = datetime.now().isoformat()
        record_id = str(uuid.uuid4())
        
        record_data = {
            "id": record_id,
            "user_id": user_id,  # The caregiver's ID
            "patient_id": record.patient_id,  # The patient's ID
            "record_type": record.record_type,
            "data": record.data,
            "created_at": current_time,
            "updated_at": current_time
        }
        
        db.collection('health_records').document(record_id).set(record_data)
        
        return record_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating health record: {str(e)}"
        )

@router.get("/patient/{patient_id}", response_model=List[HealthRecordInDB])
async def get_patient_health_records(patient_id: str, record_type: Optional[str] = None):
    try:
        # Query health records for a specific patient
        query = db.collection('health_records').where("patient_id", "==", patient_id)
        
        # Filter by record type if provided
        if record_type:
            query = query.where("record_type", "==", record_type)
        
        # Execute query
        records = [doc.to_dict() for doc in query.stream()]
        
        return records
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving health records: {str(e)}"
        )

@router.get("/{record_id}", response_model=HealthRecordInDB)
async def get_health_record(record_id: str):
    record_data = get_health_record_by_id(record_id)
    if not record_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Health record not found"
        )
    return record_data

@router.put("/{record_id}", response_model=HealthRecordInDB)
async def update_health_record(record_id: str, record_update: HealthRecordUpdate):
    try:
        # Get current record data
        record_ref = db.collection('health_records').document(record_id)
        record_doc = record_ref.get()
        
        if not record_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Health record not found"
            )
        
        # Update only provided fields
        update_data = {k: v for k, v in record_update.model_dump().items() if v is not None}
        update_data["updated_at"] = datetime.now().isoformat()
        
        # Update in Firestore
        record_ref.update(update_data)
        
        # Get updated record
        updated_record = record_ref.get().to_dict()
        return updated_record
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating health record: {str(e)}"
        )

@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_health_record(record_id: str):
    try:
        # Check if record exists
        record_ref = db.collection('health_records').document(record_id)
        record_doc = record_ref.get()
        
        if not record_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Health record not found"
            )
        
        # Delete from Firestore
        record_ref.delete()
        
        return {"detail": "Health record deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting health record: {str(e)}"
        )

# Endpoints for specific health metrics
@router.post("/metrics", response_model=HealthRecordInDB)
async def add_health_metric(metric: HealthMetric, patient_id: str, user_id: str):
    # Set timestamp if not provided
    if not metric.timestamp:
        metric.timestamp = datetime.now().isoformat()
    
    # Create a health record with the metric data
    record_create = HealthRecordCreate(
        patient_id=patient_id,
        record_type="metric",
        data=metric.model_dump()
    )
    
    return await create_health_record(record_create, user_id)

@router.post("/conditions", response_model=HealthRecordInDB)
async def add_health_condition(condition: HealthCondition, patient_id: str, user_id: str):
    # Create a health record with the condition data
    record_create = HealthRecordCreate(
        patient_id=patient_id,
        record_type="condition",
        data=condition.model_dump()
    )
    
    return await create_health_record(record_create, user_id)