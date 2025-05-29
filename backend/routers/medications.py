from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from firebase_admin import firestore
from pydantic import BaseModel, Field
from datetime import datetime, date, time, timedelta
import uuid

# Use globally initialized Firestore client
from ..main import db

# Import FieldValue for server timestamps
from google.cloud.firestore import FieldValue

from ..models.medication_model import (
    MedicationCreate, MedicationUpdate, MedicationInDB,
    MedicationLogCreate, MedicationLogInDB, MedicationSchedule, FrequencyType
)
# Import UserInDB and the authentication dependency
from .users import get_authenticated_user # Assuming get_authenticated_user is in users.py
from ..models.user_model import UserInDB # Import UserInDB

# Router for medication operations
router = APIRouter(
    prefix="/medications",
    tags=["medications"],
)

# Helper function to check if the current user is authorized to access a care profile
# Helper: Authorize if the current user can access a given care profile
async def authorize_care_profile_access(care_profile_id: str, current_user: UserInDB):
    try:
        care_profile_doc = db.collection('care_profiles').document(care_profile_id).get()
        if not care_profile_doc.exists:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Care profile not found")
        
        care_profile_data = care_profile_doc.to_dict()
        
        # Basic authorization: check if the current user created this care profile
        # More complex authorization (e.g., shared access) would need to be implemented here
        if care_profile_data.get('user_id') != current_user.id:
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this care profile")
        
        return True # Authorized

    except firestore.exceptions.FirebaseError as e:
        print(f"Firestore error during care profile authorization check: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error during authorization check")
    except HTTPException:
        raise # Re-raise HTTPException
    except Exception as e:
        print(f"Unexpected error during care profile authorization check: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during authorization check")


# Helper functions (updated to use specific exceptions and authorization)
# Helper: Get medication by ID, internal use, includes authorization
async def get_medication_by_id_internal(medication_id: str, current_user: UserInDB) -> Optional[dict]:
    try:
        medication_doc = db.collection('medications').document(medication_id).get()
        if not medication_doc.exists:
            return None # Medication not found
            
        medication_data = medication_doc.to_dict()
        
        # Authorize access to the medication's care profile
        if 'care_profile_id' in medication_data:
             await authorize_care_profile_access(medication_data['care_profile_id'], current_user)

        return medication_data

    except firestore.exceptions.FirebaseError as e:
        print(f"Database error in get_medication_by_id_internal: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error retrieving medication: {str(e)}")
    except HTTPException:
        raise # Re-raise HTTPException from authorize_care_profile_access
    except Exception as e:
        print(f"Unexpected error in get_medication_by_id_internal: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")

# Routes
# API Endpoint: Create a new medication entry
@router.post("/", response_model=MedicationInDB, status_code=status.HTTP_201_CREATED)
async def create_medication(medication_create: MedicationCreate, current_user: UserInDB = Depends(get_authenticated_user)):
    try:
        medication_id = str(uuid.uuid4())

        # Authorize access to the care profile specified in the request
        if medication_create.care_profile_id:
             await authorize_care_profile_access(medication_create.care_profile_id, current_user)

        # Convert Pydantic models to dicts for Firestore, handling date, time, and nested schedules
        medication_data_to_store = medication_create.model_dump(exclude_unset=True)
        
        # Pydantic models with date/time/datetime types should handle conversion on their own
        # when using .model_dump() with json_encoders defined in the model Config.
        # However, let's double check or add explicit conversion if needed based on how Pydantic interacts with Firestore data.
        # Firestore native timestamp/date/time types are often preferred.
        # For now, assuming Pydantic models are configured to output ISO strings for Firestore compatibility.

        firestore_data = {
            "id": medication_id,
            "user_id": current_user.id,  # User who created/manages this medication entry
            **medication_data_to_store, # Includes care_profile_id, name, schedules, dates, etc.
            "created_at": FieldValue.serverTimestamp(),
            "updated_at": FieldValue.serverTimestamp()
        }
        
        db.collection('medications').document(medication_id).set(firestore_data)
        
        # Retrieve the created document to return as MedicationInDB
        created_medication_doc = db.collection('medications').document(medication_id).get()
        if not created_medication_doc.exists:
             # This is an unexpected error if set() was successful
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve medication after creation.")

        return MedicationInDB(**created_medication_doc.to_dict())

    except HTTPException as http_exc:
        raise http_exc # Re-raise HTTPException from authorization
    except firestore.exceptions.FirebaseError as e:
        print(f"Firestore error during medication creation: {e}") # Log error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during medication creation: {str(e)}"
        )
    except Exception as e:
        print(f"Unexpected error during medication creation: {e}") # Log error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during medication creation: {str(e)}"
        )

# API Endpoint: Get all medications for a specific care profile
@router.get("/care_profile/{care_profile_id}", response_model=List[MedicationInDB])
async def get_care_profile_medications(care_profile_id: str, active_only: Optional[bool] = None, current_user: UserInDB = Depends(get_authenticated_user)):
    try:
        # Authorize access to the care profile
        await authorize_care_profile_access(care_profile_id, current_user)

        query = db.collection('medications').where("care_profile_id", "==", care_profile_id)
        
        if active_only is not None:
            query = query.where("is_active", "==", active_only)
        
        med_docs = query.stream()
        medications_list = []
        for doc in med_docs:
            med_data = doc.to_dict()
            # Pydantic model should handle conversion from Firestore timestamps/dates/times
            medications_list.append(MedicationInDB(**med_data))
        
        medications_list.sort(key=lambda x: x.name)
        
        return medications_list
    except HTTPException as http_exc:
        raise http_exc # Re-raise HTTPException from authorization
    except firestore.exceptions.FirebaseError as e:
        print(f"Firestore error retrieving medications for care_profile {care_profile_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error retrieving medications: {str(e)}"
        )
    except Exception as e:
        print(f"Unexpected error retrieving medications for care_profile {care_profile_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

# API Endpoint: Get medications scheduled for today for a specific care profile
@router.get("/today/{care_profile_id}", response_model=List[MedicationInDB])
async def get_today_medications(care_profile_id: str, current_user: UserInDB = Depends(get_authenticated_user)):
    try:
        # Authorize access to the care profile
        await authorize_care_profile_access(care_profile_id, current_user)

        now = datetime.now()
        today_date = now.date()
        today_day_str = today_date.strftime("%A") # e.g., "Monday"

        # Query for active medications belonging to the care profile
        query = db.collection('medications') \
            .where("care_profile_id", "==", care_profile_id) \
            .where("is_active", "==", True)
        
        active_medications_docs = query.stream()
        today_meds_for_response = []

        for doc in active_medications_docs:
            med_data = doc.to_dict()
            # Pydantic model handles conversion from Firestore data
            med_obj = MedicationInDB(**med_data)

            # Filter based on start_date and end_date (using date comparison)
            if med_obj.start_date and med_obj.start_date > today_date:
                continue # Medication hasn't started yet
            if med_obj.end_date and med_obj.end_date < today_date:
                continue # Medication has ended

            # Filter schedules relevant for today's date and day of week
            relevant_schedules_for_today = []
            if med_obj.schedules:
                for schedule_model in med_obj.schedules:
                    if schedule_model.frequency_type == FrequencyType.DAILY:
                        relevant_schedules_for_today.append(schedule_model)
                    elif schedule_model.frequency_type == FrequencyType.SPECIFIC_DAYS:
                        if schedule_model.days_of_week and today_day_str in schedule_model.days_of_week:
                            relevant_schedules_for_today.append(schedule_model)
                    elif schedule_model.frequency_type == FrequencyType.INTERVAL:
                        if med_obj.start_date and schedule_model.interval_days is not None:
                            # Calculate days since start date
                            delta_days = (today_date - med_obj.start_date).days
                            if delta_days >= 0 and schedule_model.interval_days > 0 and delta_days % schedule_model.interval_days == 0:
                                relevant_schedules_for_today.append(schedule_model)
                    # AS_NEEDED frequency is not time/date specific for reminders, maybe handled differently

            if relevant_schedules_for_today:
                # Create a temporary MedicationInDB object with only today's relevant schedules
                # This is to fit the response model. The frontend will use these schedules.
                temp_med_obj_for_today = med_obj.model_copy(deep=True)
                temp_med_obj_for_today.schedules = relevant_schedules_for_today
                today_meds_for_response.append(temp_med_obj_for_today)

        # Sort by the first scheduled time of the day (using time comparison)
        today_meds_for_response.sort(key=lambda m: min(s.time for s in m.schedules) if m.schedules else time.max)
        
        return today_meds_for_response
    except HTTPException as http_exc:
        raise http_exc # Re-raise HTTPException from authorization
    except firestore.exceptions.FirebaseError as e:
        print(f"Firestore error retrieving today's medications for care_profile {care_profile_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error retrieving today's medications: {str(e)}"
        )
    except Exception as e:
        print(f"Unexpected error retrieving today's medications for care_profile {care_profile_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

# API Endpoint: Get a specific medication by its ID
@router.get("/{medication_id}", response_model=MedicationInDB)
async def get_medication(medication_id: str, current_user: UserInDB = Depends(get_authenticated_user)):
    medication_data = await get_medication_by_id_internal(medication_id, current_user) # Pass current_user for auth check
    if not medication_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication not found"
        )
    # Pydantic model handles conversion from Firestore data
    return MedicationInDB(**medication_data)

# API Endpoint: Update an existing medication
@router.put("/{medication_id}", response_model=MedicationInDB)
async def update_medication(medication_id: str, medication_update: MedicationUpdate, current_user: UserInDB = Depends(get_authenticated_user)):
    try:
        medication_ref = db.collection('medications').document(medication_id)
        existing_med_doc = await get_medication_by_id_internal(medication_id, current_user) # Pass current_user for auth check
        
        if not existing_med_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medication not found"
            )
        
        # The get_medication_by_id_internal helper already performs care profile authorization.
        # Additional authorization checks specific to update might be needed here if
        # a user can view but not update a medication (not implemented in basic authz).

        update_data_dict = medication_update.model_dump(exclude_unset=True)
        
        # Pydantic model with date/time types should handle conversion to ISO strings via json_encoders.
        # However, explicit handling might be needed depending on exact model/Firestore interaction.
        # For now, assuming json_encoders work.

        # Use server timestamp for updated_at
        update_data_dict["updated_at"] = FieldValue.serverTimestamp()
        
        if not update_data_dict:
             # Return current medication data if no fields provided for update
             return MedicationInDB(**existing_med_doc)

        medication_ref.update(update_data_dict)
        
        # Get updated medication data from Firestore to return in response
        updated_medication_doc = medication_ref.get()
        if not updated_medication_doc.exists:
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve medication after update.")

        return MedicationInDB(**updated_medication_doc.to_dict())

    except HTTPException as http_exc:
        raise http_exc # Re-raise HTTPException from authorization or not found
    except firestore.exceptions.FirebaseError as e:
        print(f"Firestore error during medication update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during medication update: {str(e)}"
        )
    except Exception as e:
        print(f"Unexpected error during medication update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during medication update"
        )

# API Endpoint: Delete a medication
@router.delete("/{medication_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_medication(medication_id: str, current_user: UserInDB = Depends(get_authenticated_user)):
    try:
        medication_ref = db.collection('medications').document(medication_id)
        medication_doc = medication_ref.get()
        
        if not medication_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medication not found"
            )
        
        medication_data = medication_doc.to_dict()
        
        # Authorize access to the medication's care profile before deleting
        if 'care_profile_id' in medication_data:
             await authorize_care_profile_access(medication_data['care_profile_id'], current_user)
        
        # Delete medication document from Firestore
        medication_ref.delete()
        
        return {"detail": "Medication deleted successfully"}

    except HTTPException as http_exc:
        raise http_exc # Re-raise HTTPException from authorization or not found
    except firestore.exceptions.FirebaseError as e:
        print(f"Firestore error during medication deletion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during medication deletion: {str(e)}"
        )
    except Exception as e:
        print(f"Unexpected error during medication deletion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during medication deletion"
        )

# API Endpoint: Log that a medication has been taken and update inventory
@router.post("/log", response_model=MedicationLogInDB, status_code=status.HTTP_201_CREATED)
async def log_medication_taken(log_create: MedicationLogCreate, current_user: UserInDB = Depends(get_authenticated_user)):
    try:
        # Authorize access to the care profile specified in the log
        await authorize_care_profile_access(log_create.care_profile_id, current_user)

        medication_log_id = str(uuid.uuid4())

        # Convert Pydantic model to dict for Firestore
        log_data_to_store = log_create.model_dump(exclude_unset=True)
        
        firestore_data = {
            "id": medication_log_id,
            "user_id": current_user.id,  # User who created the log
            **log_data_to_store, # Includes medication_id, care_profile_id, timestamp, quantity, etc.
            "created_at": FieldValue.serverTimestamp(),
            "updated_at": FieldValue.serverTimestamp()
        }

        db.collection('medication_logs').document(medication_log_id).set(firestore_data)

        # --- Inventory Management ---
        # Fetch the corresponding medication document
        medication_ref = db.collection('medications').document(log_create.medication_id)
        medication_doc = medication_ref.get()

        if medication_doc.exists:
            medication_data = medication_doc.to_dict()
            current_inventory = medication_data.get('inventory_count')

            # Decrement inventory if it exists and is greater than 0
            if current_inventory is not None and current_inventory > 0:
                new_inventory = current_inventory - 1
                # Update medication document with new inventory count and updated_at timestamp
                medication_ref.update({
                    'inventory_count': new_inventory,
                    'updated_at': FieldValue.serverTimestamp()
                })
                print(f"Medication {log_create.medication_id} inventory decremented to {new_inventory}.") # Server-side log
            elif current_inventory is not None and current_inventory <= 0:
                 print(f"Attempted to log medication {log_create.medication_id} but inventory was already {current_inventory}.") # Server-side log
            else:
                 print(f"Medication {log_create.medication_id} has no inventory_count set.") # Server-side log
        else:
            print(f"Medication document {log_create.medication_id} not found when logging.") # Server-side log
        # --- End Inventory Management ---

        # Retrieve the created log document to return as MedicationLogInDB
        created_log_doc = db.collection('medication_logs').document(medication_log_id).get()
        if not created_log_doc.exists:
             # This is an unexpected error if set() was successful
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve medication log after creation.")

        return MedicationLogInDB(**created_log_doc.to_dict())

    except HTTPException as http_exc:
        raise http_exc # Re-raise HTTPException from authorization
    except firestore.exceptions.FirebaseError as e:
        print(f"Firestore error during medication log creation or inventory update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during medication logging: {str(e)}"
        )
    except Exception as e:
        print(f"Unexpected error during medication log creation or inventory update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during medication logging"
        )

# API Endpoint: Get all medication logs for a specific medication, with optional date filtering
@router.get("/log/medication/{medication_id}", response_model=List[MedicationLogInDB])
async def get_medication_logs_for_medication(medication_id: str, start_date: Optional[date] = None, end_date: Optional[date] = None, current_user: UserInDB = Depends(get_authenticated_user)):
    try:
        # Authorize access to the medication's care profile by fetching the medication first
        medication_doc = db.collection('medications').document(medication_id).get()
        if not medication_doc.exists:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medication not found.")

        medication_data = medication_doc.to_dict()
        if 'care_profile_id' in medication_data:
             await authorize_care_profile_access(medication_data['care_profile_id'], current_user)

        query = db.collection('medication_logs').where("medication_id", "==", medication_id)

        # Add date filtering if start_date or end_date are provided
        if start_date:
            # Convert date to start of day datetime for filtering
            start_datetime = datetime.combine(start_date, datetime.min.time())
            query = query.where("timestamp", ">=", start_datetime)
        if end_date:
            # Convert date to end of day datetime for filtering
            end_datetime = datetime.combine(end_date, datetime.max.time())
            query = query.where("timestamp", "<=", end_datetime)
            
        # Order by timestamp (optional but good practice for logs)
        query = query.order_by("timestamp")

        log_docs = query.stream()
        medication_logs_list = []
        for doc in log_docs:
            log_data = doc.to_dict()
            # Pydantic model handles conversion from Firestore data
            medication_logs_list.append(MedicationLogInDB(**log_data))
        
        return medication_logs_list

    except HTTPException as http_exc:
        raise http_exc # Re-raise HTTPException from authorization or not found
    except firestore.exceptions.FirebaseError as e:
        print(f"Firestore error retrieving medication logs for medication {medication_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error retrieving medication logs: {str(e)}"
        )
    except Exception as e:
        print(f"Unexpected error retrieving medication logs for medication {medication_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred retrieving medication logs"
        )

# API Endpoint: Get all medication logs for a specific care profile, with optional date filtering
@router.get("/log/care_profile/{care_profile_id}", response_model=List[MedicationLogInDB])
async def get_care_profile_medication_logs(care_profile_id: str, start_date: Optional[date] = None, end_date: Optional[date] = None, current_user: UserInDB = Depends(get_authenticated_user)):
    try:
        # Authorize access to the care profile
        await authorize_care_profile_access(care_profile_id, current_user)

        query = db.collection('medication_logs').where("care_profile_id", "==", care_profile_id)

        # Add date filtering if start_date or end_date are provided
        if start_date:
            # Convert date to start of day datetime for filtering
            start_datetime = datetime.combine(start_date, datetime.min.time())
            query = query.where("timestamp", ">=", start_datetime)
        if end_date:
            # Convert date to end of day datetime for filtering
            end_datetime = datetime.combine(end_date, datetime.max.time())
            query = query.where("timestamp", "<=", end_datetime)
            
        # Order by timestamp (optional but good practice for logs)
        query = query.order_by("timestamp")

        log_docs = query.stream()
        medication_logs_list = []
        for doc in log_docs:
            log_data = doc.to_dict()
            # Pydantic model handles conversion from Firestore data
            medication_logs_list.append(MedicationLogInDB(**log_data))
        
        return medication_logs_list

    except HTTPException as http_exc:
        raise http_exc # Re-raise HTTPException from authorization
    except firestore.exceptions.FirebaseError as e:
        print(f"Firestore error retrieving medication logs for care_profile {care_profile_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error retrieving medication logs: {str(e)}"
        )
    except Exception as e:
        print(f"Unexpected error retrieving medication logs for care_profile {care_profile_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred retrieving medication logs"
        )