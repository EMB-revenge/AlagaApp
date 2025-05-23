from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from firebase_admin import firestore
import uuid

# Import models
from ..models.health_record_model import (
    HealthRecordBase,
    HealthRecordCreate,
    HealthRecordUpdate,
    HealthRecordInDB,
    RecordType # Assuming RecordType enum is in health_record_model
)
from ..models.user_model import UserInDB # For current_user dependency
# Import authentication dependency and authorization helper from users router
from .users import get_authenticated_user, authorize_care_profile_access # Assuming these are in users.py

# Import FieldValue for server timestamps
from google.cloud.firestore import FieldValue

# Use globally initialized Firestore client
from ..main import db

router = APIRouter(
    prefix="/health-records",
    tags=["health_records"],
    responses={404: {"description": "Not found"}},
)

# Helper functions (updated for authorization, error handling, and removed db_client param)
async def get_health_record_by_id(record_id: str, current_user: UserInDB) -> Optional[HealthRecordInDB]:
    """Get a health record by ID and check authorization"""
    try:
        record_ref = db.collection('health_records').document(record_id)
        record_doc = record_ref.get()
        
        if not record_doc.exists:
            return None # Health record not found
        
        record_data = record_doc.to_dict()
        record_data['id'] = record_doc.id # Ensure id is set from document id

        # Authorize access based on care_profile_id or user_id
        if 'care_profile_id' in record_data and record_data['care_profile_id']:
             await authorize_care_profile_access(record_data['care_profile_id'], current_user)
        elif 'user_id' in record_data and record_data['user_id'] == current_user.id:
             # Record is linked directly to the user
             pass # Authorized
        else:
             # Record is not linked to an authorized care profile or the user
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this health record")

        # Pydantic model will handle conversion from Firestore timestamps/dates
        return HealthRecordInDB(**record_data)

    except firestore.exceptions.FirebaseError as e:
        print(f"Firestore error in get_health_record_by_id: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error while fetching health record: {str(e)}")
    except HTTPException:
        raise # Re-raise HTTPException from authorization
    except Exception as e:
        print(f"Unexpected error in get_health_record_by_id: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")

# Routes (updated to use authentication, authorization, error handling, and server timestamps)
@router.post("/", response_model=HealthRecordInDB, status_code=status.HTTP_201_CREATED)
async def create_health_record(record: HealthRecordCreate, current_user: UserInDB = Depends(get_authenticated_user)):
    try:
        record_id = str(uuid.uuid4())
        
        # Authorize access to the care profile specified in the request
        if record.care_profile_id:
             await authorize_care_profile_access(record.care_profile_id, current_user)
        else:
             # Decide policy for health records without care_profile_id (personal records?)
             # If personal, they should likely be linked directly to the user_id.
             # Assuming for now records must have a care_profile_id or be linked to the user.
             # If linked to the user, ensure record.user_id is set to current_user.id
             if record.user_id is not None and record.user_id != current_user.id:
                 raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot create record for another user without a care profile.")
             if record.user_id is None:
                  record.user_id = current_user.id # Automatically set user_id if not provided and no care_profile_id

        # Convert Pydantic model to dict for Firestore
        record_data_to_store = record.model_dump(exclude_unset=True)
        
        # Ensure user_id is explicitly set from authenticated user if not already
        record_data_to_store["user_id"] = current_user.id

        # Pydantic models with date/datetime types and json_encoders should
        # handle conversion to Firestore-compatible formats.

        firestore_data = {
            "id": record_id,
            **record_data_to_store, # Includes user_id, care_profile_id, record_type, date_recorded, value, unit, notes, etc.
            "created_at": FieldValue.serverTimestamp(),
            "updated_at": FieldValue.serverTimestamp()
        }

        db.collection('health_records').document(record_id).set(firestore_data)
        
        # Retrieve the created document to return as HealthRecordInDB
        created_record_doc = db.collection('health_records').document(record_id).get()
        if not created_record_doc.exists:
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve health record after creation.")

        return HealthRecordInDB(**created_record_doc.to_dict())

    except HTTPException as http_exc:
        raise http_exc # Re-raise HTTPException from authorization or bad request
    except firestore.exceptions.FirebaseError as e:
        print(f"Firestore error during health record creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during health record creation: {str(e)}"
        )
    except Exception as e:
        print(f"Unexpected error during health record creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during health record creation: {str(e)}"
        )

@router.get("/care-profile/{care_profile_id}", response_model=List[HealthRecordInDB])
async def get_care_profile_health_records(
    care_profile_id: str,
    record_type: Optional[RecordType] = Query(None), # Use Query for optional parameters
    current_user: UserInDB = Depends(get_authenticated_user)
):
    try:
        # Authorize access to the care profile
        await authorize_care_profile_access(care_profile_id, current_user)

        query = db.collection('health_records').where("care_profile_id", "==", care_profile_id)
        
        # Filter by record type if provided
        if record_type:
            query = query.where("record_type", "==", record_type.value)
        
        # Execute query
        records = []
        for doc in query.stream():
            record_data = doc.to_dict()
            record_data['id'] = doc.id
            # Pydantic model handles conversion from Firestore data
            records.append(HealthRecordInDB(**record_data))
        
        return records
    except HTTPException as http_exc:
        raise http_exc # Re-raise HTTPException from authorization
    except firestore.exceptions.FirebaseError as e:
        print(f"Firestore error retrieving health records: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error retrieving health records: {str(e)}"
        )
    except Exception as e:
        print(f"Unexpected error retrieving health records: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.get("/{record_id}", response_model=HealthRecordInDB)
async def get_health_record(record_id: str, current_user: UserInDB = Depends(get_authenticated_user)):
    # Use the helper function which includes authorization
    record_obj = await get_health_record_by_id(record_id, current_user)
    if not record_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Health record not found"
        )
    
    # Authorization check is handled within get_health_record_by_id

    return record_obj

@router.put("/{record_id}", response_model=HealthRecordInDB)
async def update_health_record(record_id: str, record_update: HealthRecordUpdate, current_user: UserInDB = Depends(get_authenticated_user)):
    try:
        # Use the helper function to get the existing record and perform authorization check
        existing_record = await get_health_record_by_id(record_id, current_user)
        if not existing_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Health record not found"
            )
        
        # Authorization check is handled by get_health_record_by_id.
        # Additional checks if certain fields require specific permissions could go here.

        update_data = record_update.model_dump(exclude_unset=True)
        
        if not update_data:
             return existing_record # Return current record if no updates provided

        # Use server timestamp for updated_at
        update_data["updated_at"] = FieldValue.serverTimestamp()
    
        record_ref = db.collection('health_records').document(record_id)
        record_ref.update(update_data)
        
        # Retrieve the updated document to return
        updated_doc = record_ref.get()
        if not updated_doc.exists:
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve health record after update.")

        updated_record_data = updated_doc.to_dict()
        updated_record_data['id'] = updated_doc.id
        return HealthRecordInDB(**updated_record_data)
    except HTTPException as http_exc:
        raise http_exc # Re-raise HTTPException from authorization or not found
    except firestore.exceptions.FirebaseError as e:
        print(f"Firestore error during health record update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during health record update: {str(e)}"
        )
    except Exception as e:
        print(f"Unexpected error during health record update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during health record update"
        )

@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_health_record(record_id: str, current_user: UserInDB = Depends(get_authenticated_user)):
    try:
        # Use the helper function to get the existing record and perform authorization check
        existing_record = await get_health_record_by_id(record_id, current_user)
        if not existing_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Health record not found"
            )

        # Authorization check is handled by get_health_record_by_id.

        record_ref = db.collection('health_records').document(record_id)
        record_ref.delete()
        
        return # Return None for 204 No Content
    except HTTPException as http_exc:
        raise http_exc # Re-raise HTTPException from authorization or not found
    except firestore.exceptions.FirebaseError as e:
        print(f"Firestore error during health record deletion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during health record deletion: {str(e)}"
        )
    except Exception as e:
        print(f"Unexpected error during health record deletion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during health record deletion"
        )

# Removed old /metrics and /conditions endpoints as they are superseded by the main / endpoint
# and the flexibility of the HealthRecordCreate model.
# If specific endpoints for certain record types are needed, they should be added following
# the pattern of the main endpoints and using the updated models.