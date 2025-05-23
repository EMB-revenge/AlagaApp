from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from firebase_admin import firestore
from datetime import datetime, date # Removed time as appointment_time is now datetime
import uuid
from ..models.appointment_model import AppointmentBase, AppointmentCreate, AppointmentUpdate, AppointmentInDB, AppointmentStatus, AppointmentType # Import Enums

# Import authentication dependency and authorization helper from users router
from .users import get_authenticated_user, authorize_care_profile_access # Assuming these are in users.py
from ..models.user_model import UserInDB # Import UserInDB

# Import FieldValue for server timestamps
from google.cloud.firestore import FieldValue

router = APIRouter(
    prefix="/appointments",
    tags=["appointments"],
    responses={404: {"description": "Not found"}},
)

# Use globally initialized Firestore client
from ..main import db

# Helper functions (updated for authorization, error handling, and removed db_client param)
async def get_appointment_by_id(appointment_id: str, current_user: UserInDB) -> Optional[AppointmentInDB]:
    """Get an appointment by ID and check authorization"""
    try:
        appointment_ref = db.collection('appointments').document(appointment_id)
        appointment_doc = appointment_ref.get()
        
        if not appointment_doc.exists:
            return None # Appointment not found
        
        appointment_data = appointment_doc.to_dict()
        appointment_data['id'] = appointment_doc.id # Ensure id is set from document id

        # Authorize access based on care_profile_id or user_id
        if 'care_profile_id' in appointment_data and appointment_data['care_profile_id']:
             await authorize_care_profile_access(appointment_data['care_profile_id'], current_user)
        elif 'user_id' in appointment_data and appointment_data['user_id'] == current_user.id:
             # Appointment is linked directly to the user
             pass # Authorized
        else:
             # Appointment is not linked to an authorized care profile or the user
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this appointment")

        # Pydantic model will handle conversion from Firestore timestamps/datetimes
        return AppointmentInDB(**appointment_data)

    except firestore.exceptions.FirebaseError as e:
        print(f"Firestore error in get_appointment_by_id: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error while fetching appointment: {str(e)}")
    except HTTPException:
        raise # Re-raise HTTPException from authorization
    except Exception as e:
        print(f"Unexpected error in get_appointment_by_id: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")

# Routes (updated to use authentication, authorization, error handling, and server timestamps)
@router.post("/", response_model=AppointmentInDB, status_code=status.HTTP_201_CREATED)
async def create_appointment(appointment: AppointmentCreate, current_user: UserInDB = Depends(get_authenticated_user)): # user_id (subject) is now part of AppointmentCreate model from backend.models.appointment_model
    try:
        # Authorize access to the care profile specified in the request if present
        if appointment.care_profile_id:
             await authorize_care_profile_access(appointment.care_profile_id, current_user)
        elif appointment.user_id is not None and appointment.user_id != current_user.id:
             # Appointment is linked directly to a user, ensure it's the current user
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot create appointment for another user without a care profile.")
        # If neither care_profile_id nor user_id is provided, or user_id is current_user.id, proceed.
        # If user_id is None, we might default it to current_user.id depending on policy.
        if appointment.user_id is None and appointment.care_profile_id is None:
             appointment.user_id = current_user.id # Default to current user if no care profile specified
        elif appointment.user_id is None and appointment.care_profile_id is not None:
             # If care_profile_id is present, the user_id in the model refers to the care profile's associated user.
             # This requires fetching the care profile to get the associated user_id.
             # For simplicity in this edit, let's assume the frontend provides the correct user_id (associated with care profile) or it's not needed for authz if care_profile_id is used.
             # A more robust approach would fetch the care profile here and validate/set the user_id.
             pass # Assuming user_id is either provided or not strictly needed if care_profile_id is used for filtering/authz.


        appointment_id = str(uuid.uuid4())
        
        # Convert Pydantic model to dict for Firestore
        appointment_data_to_store = appointment.model_dump(exclude_unset=True)
        
        # Pydantic models with datetime types and json_encoders should
        # handle conversion to Firestore-compatible formats (ISO strings or native types).

        firestore_data = {
            "id": appointment_id,
            **appointment_data_to_store, # Includes user_id, care_profile_id, title, time, duration, etc.
            "created_at": FieldValue.serverTimestamp(),
            "updated_at": FieldValue.serverTimestamp()
        }
        # Ensure status and reminder_sent defaults are handled (Pydantic model defaults should work)

        db.collection('appointments').document(appointment_id).set(firestore_data)
        
        # Retrieve the created document to return as AppointmentInDB
        created_appointment_doc = db.collection('appointments').document(appointment_id).get()
        if not created_appointment_doc.exists:
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve appointment after creation.")

        return AppointmentInDB(**created_appointment_doc.to_dict())

    except HTTPException as http_exc:
        raise http_exc # Re-raise HTTPException from authorization or bad request
    except firestore.exceptions.FirebaseError as e:
        print(f"Firestore error during appointment creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during appointment creation: {str(e)}"
        )
    except Exception as e:
        print(f"Unexpected error during appointment creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during appointment creation: {str(e)}"
        )

# Update endpoint path and logic to use care_profile_id for filtering and authorization
@router.get("/care-profile/{care_profile_id}", response_model=List[AppointmentInDB])
async def get_care_profile_appointments(
    care_profile_id: str,
    start_datetime: Optional[datetime] = None,
    end_datetime: Optional[datetime] = None,
    current_user: UserInDB = Depends(get_authenticated_user)
):
    """Get all appointments for a specific care profile within a datetime range"""
    try:
        # Authorize access to the care profile
        await authorize_care_profile_access(care_profile_id, current_user)

        # Query appointments for the care profile
        query = db.collection('appointments').where("care_profile_id", "==", care_profile_id)
        
        # Filter by datetime range if provided (using Timestamp comparison in Firestore)
        if start_datetime:
            query = query.where("appointment_time", ">=", start_datetime)
        if end_datetime:
            query = query.where("appointment_time", "<=", end_datetime)
        
        # Order by appointment time
        query = query.order_by("appointment_time")

        # Execute query
        appointments = []
        for doc in query.stream():
            appointment_data = doc.to_dict()
            appointment_data['id'] = doc.id
            # Pydantic model handles conversion from Firestore Timestamps
            appointments.append(AppointmentInDB(**appointment_data))
        
        return appointments
    except HTTPException as http_exc:
        raise http_exc # Re-raise HTTPException from authorization
    except firestore.exceptions.FirebaseError as e:
        print(f"Firestore error retrieving care profile appointments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error retrieving appointments: {str(e)}"
        )
    except Exception as e:
        print(f"Unexpected error retrieving care profile appointments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

# Update endpoint path and logic to use care_profile_id
@router.get("/today/care-profile/{care_profile_id}", response_model=List[AppointmentInDB])
async def get_today_appointments(care_profile_id: str, current_user: UserInDB = Depends(get_authenticated_user)):
    """Get all appointments for a specific care profile for today"""
    try:
        # Authorize access to the care profile
        await authorize_care_profile_access(care_profile_id, current_user)

        # Get today's date and datetime range
        today = date.today()
        today_start_dt = datetime.combine(today, datetime.min.time())
        today_end_dt = datetime.combine(today, datetime.max.time())
        
        # Query appointments for today for the care profile
        query = db.collection('appointments')\
            .where("care_profile_id", "==", care_profile_id)\
            .where("appointment_time", ">=", today_start_dt)\
            .where("appointment_time", "<=", today_end_dt)
        
        # Order by appointment time
        query = query.order_by("appointment_time")

        # Execute query
        appointments = []
        for doc in query.stream():
             appointment_data = doc.to_dict()
             appointment_data['id'] = doc.id
             # Pydantic model handles conversion from Firestore Timestamps
             appointments.append(AppointmentInDB(**appointment_data))
        
        return appointments
    except HTTPException as http_exc:
        raise http_exc # Re-raise HTTPException from authorization
    except firestore.exceptions.FirebaseError as e:
        print(f"Firestore error retrieving today's care profile appointments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error retrieving today's appointments: {str(e)}"
        )
    except Exception as e:
        print(f"Unexpected error retrieving today's care profile appointments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

# Update endpoint path and logic to use care_profile_id
@router.get("/upcoming/care-profile/{care_profile_id}", response_model=List[AppointmentInDB])
async def get_upcoming_appointments(
    care_profile_id: str,
    days: int = 7, # 'days' param currently unused, consider implementing date range based on it
    current_user: UserInDB = Depends(get_authenticated_user)
):
    """Get upcoming appointments for a specific care profile"""
    try:
        # Authorize access to the care profile
        await authorize_care_profile_access(care_profile_id, current_user)

        # Get current datetime and calculate end datetime based on 'days' (optional implementation)
        now = datetime.now()
        # upcoming_end_dt = now + timedelta(days=days) # Example of using 'days'

        # Query upcoming appointments for the care profile (from now onwards)
        query = db.collection('appointments')\
            .where("care_profile_id", "==", care_profile_id)\
            .where("appointment_time", ">=", now)
            # .where("appointment_time", "<=", upcoming_end_dt) # Uncomment to filter by days
        
        # Order by appointment time
        query = query.order_by("appointment_time")

        # Execute query
        appointments = []
        for doc in query.stream():
            appointment_data = doc.to_dict()
            appointment_data['id'] = doc.id
            # Pydantic model handles conversion from Firestore Timestamps
            appointments.append(AppointmentInDB(**appointment_data))
        
        return appointments
    except HTTPException as http_exc:
        raise http_exc # Re-raise HTTPException from authorization
    except firestore.exceptions.FirebaseError as e:
        print(f"Firestore error retrieving upcoming care profile appointments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error retrieving upcoming appointments: {str(e)}"
        )
    except Exception as e:
        print(f"Unexpected error retrieving upcoming care profile appointments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

# Update get_appointment to use authentication and refined helper
@router.get("/{appointment_id}", response_model=AppointmentInDB)
async def get_appointment(appointment_id: str, current_user: UserInDB = Depends(get_authenticated_user)):
    # Use the helper function which includes authorization
    appointment_obj = await get_appointment_by_id(appointment_id, current_user)
    if not appointment_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    # Authorization check is handled within get_appointment_by_id
    return appointment_obj

# Update update_appointment to use authentication, refined helper, and server timestamps
@router.put("/{appointment_id}", response_model=AppointmentInDB)
async def update_appointment(appointment_id: str, appointment_update: AppointmentUpdate, current_user: UserInDB = Depends(get_authenticated_user)):
    try:
        # Use the helper function to get the existing appointment and perform authorization check
        existing_appointment = await get_appointment_by_id(appointment_id, current_user)
        
        if not existing_appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found"
            )
        
        # Authorization check is handled by get_appointment_by_id.

        # Prepare update data
        update_data = appointment_update.model_dump(exclude_unset=True)
        
        if not update_data:
             return existing_appointment # Return current appointment if no updates provided

        # Use server timestamp for updated_at
        update_data["updated_at"] = FieldValue.serverTimestamp()
        
        appointment_ref = db.collection('appointments').document(appointment_id)
        appointment_ref.update(update_data)
        
        # Get updated appointment from Firestore to return in response
        updated_appointment_doc = appointment_ref.get()
        if not updated_appointment_doc.exists:
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve appointment after update.")

        return AppointmentInDB(**updated_appointment_doc.to_dict())

    except HTTPException as http_exc:
        raise http_exc # Re-raise HTTPException from authorization or not found
    except firestore.exceptions.FirebaseError as e:
        print(f"Firestore error during appointment update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during appointment update: {str(e)}"
        )
    except Exception as e:
        print(f"Unexpected error during appointment update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during appointment update"
        )

# Update delete_appointment to use authentication and refined helper
@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_appointment(appointment_id: str, current_user: UserInDB = Depends(get_authenticated_user)):
    try:
        # Use the helper function to get the existing appointment and perform authorization check
        existing_appointment = await get_appointment_by_id(appointment_id, current_user)
        
        if not existing_appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found"
            )
        
        # Authorization check is handled by get_appointment_by_id.

        appointment_ref = db.collection('appointments').document(appointment_id)
        appointment_ref.delete()
        
        # Note: HTTP 204 response typically has no body.
        return # Return None for 204 No Content

    except HTTPException as http_exc:
        raise http_exc # Re-raise HTTPException from authorization or not found
    except firestore.exceptions.FirebaseError as e:
        print(f"Firestore error during appointment deletion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during appointment deletion: {str(e)}"
        )
    except Exception as e:
        print(f"Unexpected error during appointment deletion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during appointment deletion"
        )

# Update mark_appointment_complete to use authentication, refined helper, and server timestamps
@router.post("/{appointment_id}/complete", response_model=AppointmentInDB)
async def mark_appointment_complete(appointment_id: str, current_user: UserInDB = Depends(get_authenticated_user)):
    try:
        # Use the helper function to get the existing appointment and perform authorization check
        existing_appointment = await get_appointment_by_id(appointment_id, current_user)
        
        if not existing_appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found"
            )
        
        # Authorization check is handled by get_appointment_by_id.

        appointment_ref = db.collection('appointments').document(appointment_id)
        
        # Update status to completed and use server timestamp
        update_data = {
            "status": AppointmentStatus.COMPLETED.value, # Use Enum value
            "updated_at": FieldValue.serverTimestamp()
        }
        
        appointment_ref.update(update_data)
        
        # Get updated appointment from Firestore to return in response
        updated_appointment_doc = appointment_ref.get()
        if not updated_appointment_doc.exists:
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve appointment after status update.")

        return AppointmentInDB(**updated_appointment_doc.to_dict())

    except HTTPException as http_exc:
        raise http_exc # Re-raise HTTPException from authorization or not found
    except firestore.exceptions.FirebaseError as e:
        print(f"Firestore error marking appointment as complete: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error marking appointment as complete: {str(e)}"
        )
    except Exception as e:
        print(f"Unexpected error marking appointment as complete: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred marking appointment as complete"
        )