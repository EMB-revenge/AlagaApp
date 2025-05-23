from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional, Union # Import Union for optional types in models
from firebase_admin import firestore
from datetime import datetime, date # Import date as well if vital signs can have date-only timestamps
import uuid

# Use globally initialized Firestore client
from ..main import db
# from ..models.vital_sign_model import ( # Remove incorrect import
#     VitalSignCreate, VitalSignUpdate, VitalSignInDB, VitalSignType, BloodPressureValue
# )
# Import Health Record models and Vital Sign specific types from health_record_model
from ..models.health_record_model import (\
    HealthRecordCreate, HealthRecordUpdate, HealthRecordInDB, \
    VitalSignType, BloodPressureValue, RecordType # Import RecordType as well
)
# Import UserInDB and authentication/authorization dependencies
from .users import get_authenticated_user, authorize_care_profile_access # Assuming these are in users.py
from ..models.user_model import UserInDB # Import UserInDB

# Import FieldValue for server timestamps
from google.cloud.firestore import FieldValue

router = APIRouter(
    prefix="/vitals",
    tags=["vitals"],
    responses={404: {"description": "Not found"}},
)

# Helper function to get a vital sign (which is a type of HealthRecord) by ID with authorization check
async def get_vital_by_id_authorized(vital_id: str, current_user: UserInDB) -> Optional[HealthRecordInDB]: # Use HealthRecordInDB
    """Get a vital sign (health record) by ID and check authorization"""
    try:
        vital_ref = db.collection('vital_signs').document(vital_id)
        vital_doc = await vital_ref.get() # Use await with async get()
        
        if not vital_doc.exists:
            return None # Vital sign (health record) not found
        
        vital_data = vital_doc.to_dict()
        vital_data['id'] = vital_doc.id # Ensure id is set from document id

        # Authorize access based on care_profile_id or user_id
        if 'care_profile_id' in vital_data and vital_data['care_profile_id']:
             await authorize_care_profile_access(vital_data['care_profile_id'], current_user)
        elif 'user_id' in vital_data and vital_data['user_id'] == current_user.id:
             # Vital sign is linked directly to the user
             pass # Authorized
        else:
             # Vital sign is not linked to an authorized care profile or the user
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this vital sign (health record)")

        # Pydantic model will handle conversion from Firestore timestamps/datetimes/nested types
        # Ensure the record_type is one of the vital sign types if this helper is specific to vitals
        if vital_data.get('record_type') not in [e.value for e in VitalSignType]: # Check if it's a vital sign type
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Health record found but is not a vital sign.")

        return HealthRecordInDB(**vital_data) # Use HealthRecordInDB

    except firestore.exceptions.FirebaseError as e:
        print(f"Firestore error in get_vital_by_id_authorized: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error while fetching vital sign (health record): {str(e)}")
    except HTTPException:
        raise # Re-raise HTTPException from authorization or not found check
    except Exception as e:
        print(f"Unexpected error in get_vital_by_id_authorized: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")

# Routes
@router.post("/", response_model=HealthRecordInDB, status_code=status.HTTP_201_CREATED) # Use HealthRecordInDB
async def create_vital_sign(vital_create: HealthRecordCreate, current_user: UserInDB = Depends(get_authenticated_user)): # Use HealthRecordCreate
    try:
        vital_id = str(uuid.uuid4())

        # Authorize access to the care profile specified in the request if present
        if vital_create.care_profile_id:
             await authorize_care_profile_access(vital_create.care_profile_id, current_user)
        elif vital_create.user_id is not None and vital_create.user_id != current_user.id:
             # Vital sign is linked directly to a user, ensure it's the current user
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot create vital sign (health record) for another user without a care profile.")
        # If neither care_profile_id nor user_id is provided, or user_id is current_user.id, proceed.
        # If user_id is None, we might default it to current_user.id depending on policy.
        if vital_create.user_id is None and vital_create.care_profile_id is None:
             vital_create.user_id = current_user.id # Default to current user if no care profile specified
        elif vital_create.user_id is None and vital_create.care_profile_id is not None:
             # If care_profile_id is present, the user_id in the model refers to the care profile's associated user.
             # This requires fetching the care profile to get the associated user_id. (Not implementing fetching here for simplicity)
             # Assuming user_id is either provided or not strictly needed if care_profile_id is used for authz.
             pass # Assuming user_id is either provided or not strictly needed if care_profile_id is used for filtering/authz.

        # Convert Pydantic model to dict for Firestore
        # Pydantic model with json_encoders should handle conversion of datetime and nested models
        vital_data_to_store = vital_create.model_dump(exclude_unset=True)

        # Ensure user_id is explicitly set from authenticated user if not already
        vital_data_to_store["user_id"] = current_user.id

        # Optional: Validate that record_type is a vital sign type
        if vital_data_to_store.get('record_type') not in [e.value for e in VitalSignType]:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Record type must be a valid vital sign type.")

        firestore_data = {
            "id": vital_id,
            **vital_data_to_store, # Includes user_id, care_profile_id, type, timestamp, value, unit, notes, etc.
            "created_at": FieldValue.serverTimestamp(),
            "updated_at": FieldValue.serverTimestamp()
        }

        await db.collection('vital_signs').document(vital_id).set(firestore_data) # Use await
        
        # Retrieve the created document to return as HealthRecordInDB
        # Use get_vital_by_id_authorized helper to retrieve and authorize the newly created document
        created_vital_obj = await get_vital_by_id_authorized(vital_id, current_user)
        if not created_vital_obj:
             # This is an unexpected error if set() was successful and authz passes
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve vital sign (health record) after creation.")

        return created_vital_obj

    except HTTPException as http_exc:
        raise http_exc # Re-raise HTTPException from authorization or bad request
    except firestore.exceptions.FirebaseError as e:
        print(f"Firestore error during vital sign creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during vital sign creation: {str(e)}"
        )
    except Exception as e:
        print(f"Unexpected error during vital sign creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.get("/care_profile/{care_profile_id}", response_model=List[HealthRecordInDB]) # Use List[HealthRecordInDB]
async def get_care_profile_vital_signs(
    care_profile_id: str,
    vital_type: Optional[VitalSignType] = None,
    start_datetime: Optional[datetime] = None, # Use datetime for range queries
    end_datetime: Optional[datetime] = None,   # Use datetime for range queries
    current_user: UserInDB = Depends(get_authenticated_user)
):
    try:
        # Authorize access to the care profile
        await authorize_care_profile_access(care_profile_id, current_user)

        # Query for health records associated with the care profile that are also vital signs
        query = db.collection('vital_signs') # Assuming vital signs are stored in a 'vital_signs' collection, adjust if they are in 'health_records'
        query = query.where("care_profile_id", "==", care_profile_id)
        # .where("record_type", "in", [e.value for e in VitalSignType]) # Filter by vital sign types if needed
        
        if vital_type:
            query = query.where("type", "==", vital_type.value) # Use .value for Enum
        
        # Filter by datetime range on the 'timestamp' field
        if start_datetime:
            query = query.where("timestamp", ">=", start_datetime)
        if end_datetime:
            query = query.where("timestamp", "<=", end_datetime)
        
        vital_docs = await query.order_by("timestamp", direction=firestore.Query.DESCENDING).stream() # Use await
        vitals_list = []
        # Use async for with stream()
        async for doc in vital_docs:
            vital_data = doc.to_dict()
            vital_data['id'] = doc.id # Ensure id is set
            # Pydantic model handles conversion from Firestore timestamps/datetimes/nested types
            vitals_list.append(HealthRecordInDB(**vital_data)) # Use HealthRecordInDB
        
        return vitals_list

    except HTTPException as http_exc:
        raise http_exc # Re-raise HTTPException from authorization
    except firestore.exceptions.FirebaseError as e:
        print(f"Firestore error retrieving vital signs for care_profile {care_profile_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error retrieving vital signs: {str(e)}"
        )
    except Exception as e:
        print(f"Unexpected error retrieving vital signs for care_profile {care_profile_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.get("/{vital_id}", response_model=HealthRecordInDB) # Use HealthRecordInDB
async def get_vital_sign(vital_id: str, current_user: UserInDB = Depends(get_authenticated_user)):
    # Use the helper function which includes authorization
    vital_obj = await get_vital_by_id_authorized(vital_id, current_user)
    if not vital_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vital sign (health record) not found"
        )
    # Authorization check is handled within get_vital_by_id_authorized
    return vital_obj

@router.put("/{vital_id}", response_model=HealthRecordInDB) # Use HealthRecordInDB
async def update_vital_sign(vital_id: str, vital_update: HealthRecordUpdate, current_user: UserInDB = Depends(get_authenticated_user)): # Use HealthRecordUpdate
    try:
        vital_ref = db.collection('vital_signs').document(vital_id)
        
        # Use the helper function to get the existing vital sign and perform authorization check
        existing_vital_obj = await get_vital_by_id_authorized(vital_id, current_user)
        
        if not existing_vital_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vital sign (health record) not found" # Helper raises 403 if unauthorized, so 404 means not found or not accessible
            )
        
        # Authorization check is handled by get_vital_by_id_authorized.
        # Additional checks if certain fields require specific permissions could go here.

        update_data_dict = vital_update.model_dump(exclude_unset=True)
        
        if not update_data_dict:
             return existing_vital_obj # Return current vital sign if no updates provided

        # Use server timestamp for updated_at
        update_data_dict["updated_at"] = FieldValue.serverTimestamp()
        
        await vital_ref.update(update_data_dict) # Use await
        
        # Retrieve the updated document to return
        # Use the helper function to retrieve and authorize the updated document
        updated_vital_obj = await get_vital_by_id_authorized(vital_id, current_user)
        if not updated_vital_obj:
             # This is an unexpected error if update() was successful and authz passes
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve vital sign (health record) after update.")

        return updated_vital_obj

    except HTTPException as http_exc:
        raise http_exc # Re-raise HTTPException from authorization or not found
    except firestore.exceptions.FirebaseError as e:
        print(f"Firestore error during vital sign update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during vital sign update: {str(e)}"
        )
    except Exception as e:
        print(f"Unexpected error during vital sign update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during vital sign update: {str(e)}"
        )

@router.delete("/{vital_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vital_sign(vital_id: str, current_user: UserInDB = Depends(get_authenticated_user)): # Use UserInDB
    try:
        vital_ref = db.collection('vital_signs').document(vital_id)
        
        # Use the helper function to get the existing vital sign and perform authorization check
        existing_vital_obj = await get_vital_by_id_authorized(vital_id, current_user)
        
        if not existing_vital_obj:
            # Helper raises 403 if unauthorized, so 404 means not found or not accessible
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vital sign (health record) not found"
            )
        
        # Authorization check is handled by get_vital_by_id_authorized.

        await vital_ref.delete() # Use await
        
        return # Return None for 204 No Content

    except HTTPException as http_exc:
        raise http_exc # Re-raise HTTPException from authorization or not found
    except firestore.exceptions.FirebaseError as e:
        print(f"Firestore error during vital sign deletion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during vital sign deletion: {str(e)}"
        )
    except Exception as e:
        print(f"Unexpected error during vital sign deletion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during vital sign deletion: {str(e)}"
        )