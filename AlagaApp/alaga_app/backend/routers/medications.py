from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from firebase_admin import firestore
from pydantic import BaseModel, Field
from datetime import datetime, date, time
import uuid

router = APIRouter(
    prefix="/medications",
    tags=["medications"],
)

# Use globally initialized Firestore client
from ..main import db

# Models
class MedicationSchedule(BaseModel):
    time: str  # ISO format time
    days: List[str] = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    dosage: str

class MedicationBase(BaseModel):
    patient_id: str
    name: str
    dosage_unit: str  # e.g., "mg", "ml", "tablet"
    instructions: Optional[str] = None
    start_date: Optional[str] = None  # ISO format date
    end_date: Optional[str] = None  # ISO format date
    schedules: List[MedicationSchedule] = []
    refill_reminder: Optional[bool] = False
    refill_date: Optional[str] = None  # ISO format date
    prescribing_doctor: Optional[str] = None
    pharmacy: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True

class MedicationCreate(MedicationBase):
    pass

class MedicationUpdate(BaseModel):
    name: Optional[str] = None
    dosage_unit: Optional[str] = None
    instructions: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    schedules: Optional[List[MedicationSchedule]] = None
    refill_reminder: Optional[bool] = None
    refill_date: Optional[str] = None
    prescribing_doctor: Optional[str] = None
    pharmacy: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None

class MedicationInDB(MedicationBase):
    id: str
    user_id: str  # ID of the caregiver who created the medication
    created_at: str
    updated_at: str

class MedicationLog(BaseModel):
    medication_id: str
    patient_id: str
    taken_at: str  # ISO format datetime
    scheduled_time: str  # ISO format time
    dosage: str
    notes: Optional[str] = None
    was_taken: bool = True

class MedicationLogCreate(BaseModel):
    medication_id: str
    scheduled_time: str
    dosage: str
    notes: Optional[str] = None
    was_taken: bool = True

class MedicationLogInDB(MedicationLog):
    id: str
    user_id: str  # ID of the caregiver who logged the medication
    created_at: str

# Helper functions
def get_medication_by_id(medication_id: str):
    try:
        medication_doc = db.collection('medications').document(medication_id).get()
        if medication_doc.exists:
            return medication_doc.to_dict()
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Routes
@router.post("/", response_model=MedicationInDB, status_code=status.HTTP_201_CREATED)
async def create_medication(medication: MedicationCreate, user_id: str):
    try:
        # Create medication in Firestore
        current_time = datetime.now().isoformat()
        medication_id = str(uuid.uuid4())
        
        medication_data = {
            "id": medication_id,
            "user_id": user_id,
            **medication.model_dump(),
            "created_at": current_time,
            "updated_at": current_time
        }
        
        db.collection('medications').document(medication_id).set(medication_data)
        
        return medication_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating medication: {str(e)}"
        )

@router.get("/patient/{patient_id}", response_model=List[MedicationInDB])
async def get_patient_medications(patient_id: str, active_only: bool = False):
    try:
        # Query medications for a specific patient
        query = db.collection('medications').where("patient_id", "==", patient_id)
        
        # Filter by active status if requested
        if active_only:
            query = query.where("is_active", "==", True)
        
        # Execute query
        medications = [doc.to_dict() for doc in query.stream()]
        
        # Sort by name
        medications.sort(key=lambda x: x["name"])
        
        return medications
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving medications: {str(e)}"
        )

@router.get("/today/{patient_id}", response_model=List[dict])
async def get_today_medications(patient_id: str):
    try:
        # Get today's day of the week
        today_day = datetime.now().strftime("%A")
        
        # Query active medications for the patient
        query = db.collection('medications').where("patient_id", "==", patient_id).where("is_active", "==", True)
        
        # Execute query
        medications = [doc.to_dict() for doc in query.stream()]
        
        # Filter schedules for today and format response
        today_meds = []
        for med in medications:
            today_schedules = []
            for schedule in med.get("schedules", []):
                if today_day in schedule.get("days", []):
                    today_schedules.append(schedule)
            
            if today_schedules:
                today_meds.append({
                    "id": med["id"],
                    "name": med["name"],
                    "dosage_unit": med["dosage_unit"],
                    "instructions": med.get("instructions"),
                    "schedules": today_schedules
                })
        
        # Sort by scheduled time
        today_meds.sort(key=lambda x: x["schedules"][0]["time"] if x["schedules"] else "")
        
        return today_meds
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving today's medications: {str(e)}"
        )

@router.get("/{medication_id}", response_model=MedicationInDB)
async def get_medication(medication_id: str):
    medication_data = get_medication_by_id(medication_id)
    if not medication_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication not found"
        )
    return medication_data

@router.put("/{medication_id}", response_model=MedicationInDB)
async def update_medication(medication_id: str, medication_update: MedicationUpdate):
    try:
        # Get current medication data
        medication_ref = db.collection('medications').document(medication_id)
        medication_doc = medication_ref.get()
        
        if not medication_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medication not found"
            )
        
        # Update only provided fields
        update_data = {k: v for k, v in medication_update.model_dump().items() if v is not None}
        update_data["updated_at"] = datetime.now().isoformat()
        
        # Update in Firestore
        medication_ref.update(update_data)
        
        # Get updated medication
        updated_medication = medication_ref.get().to_dict()
        return updated_medication
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating medication: {str(e)}"
        )

@router.delete("/{medication_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_medication(medication_id: str):
    try:
        # Check if medication exists
        medication_ref = db.collection('medications').document(medication_id)
        medication_doc = medication_ref.get()
        
        if not medication_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medication not found"
            )
        
        # Delete from Firestore
        medication_ref.delete()
        
        return {"detail": "Medication deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting medication: {str(e)}"
        )

# Medication logs
@router.post("/log", response_model=MedicationLogInDB, status_code=status.HTTP_201_CREATED)
async def log_medication(log: MedicationLogCreate, user_id: str):
    try:
        # Get medication data to get patient_id
        medication_data = get_medication_by_id(log.medication_id)
        if not medication_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medication not found"
            )
        
        # Create medication log in Firestore
        current_time = datetime.now().isoformat()
        log_id = str(uuid.uuid4())
        
        log_data = {
            "id": log_id,
            "user_id": user_id,
            "medication_id": log.medication_id,
            "patient_id": medication_data["patient_id"],
            "taken_at": current_time,
            "scheduled_time": log.scheduled_time,
            "dosage": log.dosage,
            "notes": log.notes,
            "was_taken": log.was_taken,
            "created_at": current_time
        }
        
        db.collection('medication_logs').document(log_id).set(log_data)
        
        return log_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error logging medication: {str(e)}"
        )

@router.get("/log/medication/{medication_id}", response_model=List[MedicationLogInDB])
async def get_medication_logs(medication_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None):
    try:
        # Query logs for a specific medication
        query = db.collection('medication_logs').where("medication_id", "==", medication_id)
        
        # Filter by date range if provided
        if start_date:
            query = query.where("taken_at", ">=", start_date)
        if end_date:
            query = query.where("taken_at", "<=", end_date)
        
        # Execute query
        logs = [doc.to_dict() for doc in query.stream()]
        
        # Sort by taken_at in descending order (newest first)
        logs.sort(key=lambda x: x["taken_at"], reverse=True)
        
        return logs
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving medication logs: {str(e)}"
        )

@router.get("/log/patient/{patient_id}", response_model=List[MedicationLogInDB])
async def get_patient_medication_logs(patient_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None):
    try:
        # Query logs for a specific patient
        query = db.collection('medication_logs').where("patient_id", "==", patient_id)
        
        # Filter by date range if provided
        if start_date:
            query = query.where("taken_at", ">=", start_date)
        if end_date:
            query = query.where("taken_at", "<=", end_date)
        
        # Execute query
        logs = [doc.to_dict() for doc in query.stream()]
        
        # Sort by taken_at in descending order (newest first)
        logs.sort(key=lambda x: x["taken_at"], reverse=True)
        
        return logs
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving patient medication logs: {str(e)}"
        )