from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from firebase_admin import firestore
from pydantic import BaseModel, Field
from datetime import datetime, date, time
import uuid

router = APIRouter(
    prefix="/appointments",
    tags=["appointments"],
)

# Use globally initialized Firestore client
from ..main import db

# Models
class AppointmentBase(BaseModel):
    patient_id: str
    title: str
    description: Optional[str] = None
    appointment_date: str  # ISO format date
    appointment_time: str  # ISO format time
    location: Optional[str] = None
    doctor_name: Optional[str] = None
    appointment_type: Optional[str] = None  # e.g., "checkup", "follow-up", "specialist"
    notes: Optional[str] = None
    is_completed: bool = False

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    appointment_date: Optional[str] = None
    appointment_time: Optional[str] = None
    location: Optional[str] = None
    doctor_name: Optional[str] = None
    appointment_type: Optional[str] = None
    notes: Optional[str] = None
    is_completed: Optional[bool] = None

class AppointmentInDB(AppointmentBase):
    id: str
    user_id: str  # ID of the caregiver who created the appointment
    created_at: str
    updated_at: str

# Helper functions
def get_appointment_by_id(appointment_id: str):
    try:
        appointment_doc = db.collection('appointments').document(appointment_id).get()
        if appointment_doc.exists:
            return appointment_doc.to_dict()
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Routes
@router.post("/", response_model=AppointmentInDB, status_code=status.HTTP_201_CREATED)
async def create_appointment(appointment: AppointmentCreate, user_id: str):
    try:
        # Create appointment in Firestore
        current_time = datetime.now().isoformat()
        appointment_id = str(uuid.uuid4())
        
        appointment_data = {
            "id": appointment_id,
            "user_id": user_id,
            **appointment.model_dump(),
            "created_at": current_time,
            "updated_at": current_time
        }
        
        db.collection('appointments').document(appointment_id).set(appointment_data)
        
        return appointment_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating appointment: {str(e)}"
        )

@router.get("/patient/{patient_id}", response_model=List[AppointmentInDB])
async def get_patient_appointments(patient_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None):
    try:
        # Query appointments for a specific patient
        query = db.collection('appointments').where("patient_id", "==", patient_id)
        
        # Filter by date range if provided
        if start_date:
            query = query.where("appointment_date", ">=", start_date)
        if end_date:
            query = query.where("appointment_date", "<=", end_date)
        
        # Execute query
        appointments = [doc.to_dict() for doc in query.stream()]
        
        # Sort by date and time
        appointments.sort(key=lambda x: (x["appointment_date"], x["appointment_time"]))
        
        return appointments
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving appointments: {str(e)}"
        )

@router.get("/today/{patient_id}", response_model=List[AppointmentInDB])
async def get_today_appointments(patient_id: str):
    try:
        # Get today's date in ISO format
        today = date.today().isoformat()
        
        # Query appointments for today
        query = db.collection('appointments').where("patient_id", "==", patient_id).where("appointment_date", "==", today)
        
        # Execute query
        appointments = [doc.to_dict() for doc in query.stream()]
        
        # Sort by time
        appointments.sort(key=lambda x: x["appointment_time"])
        
        return appointments
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving today's appointments: {str(e)}"
        )

@router.get("/upcoming/{patient_id}", response_model=List[AppointmentInDB])
async def get_upcoming_appointments(patient_id: str, days: int = 7):
    try:
        # Get today's date in ISO format
        today = date.today().isoformat()
        
        # Query appointments for the patient
        query = db.collection('appointments').where("patient_id", "==", patient_id).where("appointment_date", ">=", today)
        
        # Execute query
        appointments = [doc.to_dict() for doc in query.stream()]
        
        # Sort by date and time
        appointments.sort(key=lambda x: (x["appointment_date"], x["appointment_time"]))
        
        return appointments
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving upcoming appointments: {str(e)}"
        )

@router.get("/{appointment_id}", response_model=AppointmentInDB)
async def get_appointment(appointment_id: str):
    appointment_data = get_appointment_by_id(appointment_id)
    if not appointment_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    return appointment_data

@router.put("/{appointment_id}", response_model=AppointmentInDB)
async def update_appointment(appointment_id: str, appointment_update: AppointmentUpdate):
    try:
        # Get current appointment data
        appointment_ref = db.collection('appointments').document(appointment_id)
        appointment_doc = appointment_ref.get()
        
        if not appointment_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found"
            )
        
        # Update only provided fields
        update_data = {k: v for k, v in appointment_update.model_dump().items() if v is not None}
        update_data["updated_at"] = datetime.now().isoformat()
        
        # Update in Firestore
        appointment_ref.update(update_data)
        
        # Get updated appointment
        updated_appointment = appointment_ref.get().to_dict()
        return updated_appointment
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating appointment: {str(e)}"
        )

@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_appointment(appointment_id: str):
    try:
        # Check if appointment exists
        appointment_ref = db.collection('appointments').document(appointment_id)
        appointment_doc = appointment_ref.get()
        
        if not appointment_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found"
            )
        
        # Delete from Firestore
        appointment_ref.delete()
        
        return {"detail": "Appointment deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting appointment: {str(e)}"
        )

@router.post("/{appointment_id}/complete", response_model=AppointmentInDB)
async def mark_appointment_complete(appointment_id: str):
    try:
        # Get current appointment data
        appointment_ref = db.collection('appointments').document(appointment_id)
        appointment_doc = appointment_ref.get()
        
        if not appointment_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found"
            )
        
        # Update completion status
        update_data = {
            "is_completed": True,
            "updated_at": datetime.now().isoformat()
        }
        
        # Update in Firestore
        appointment_ref.update(update_data)
        
        # Get updated appointment
        updated_appointment = appointment_ref.get().to_dict()
        return updated_appointment
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error marking appointment as complete: {str(e)}"
        )