from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from firebase_admin import firestore
from datetime import datetime, date
import uuid

# Use globally initialized Firestore client
from ..main import db

# Import FieldValue for server timestamps
from google.cloud.firestore import FieldValue

from ..models.reminder_model import (
    ReminderCreate, ReminderUpdate, ReminderInDB, ReminderType
)
# Import UserInDB and authentication/authorization dependencies
from .users import get_authenticated_user, authorize_care_profile_access # Assuming these are in users.py
from ..models.user_model import UserInDB # Import UserInDB

router = APIRouter(
    prefix="/reminders",
    tags=["reminders"],
    responses={404: {"description": "Not found"}},
)

# Helper functions (updated for authorization and error handling)
async def get_reminder_by_id_internal(reminder_id: str, current_user: UserInDB) -> Optional[dict]:
    """Get a reminder by ID and check authorization"""
    try:
        reminder_doc = db.collection('reminders').document(reminder_id).get()
        if not reminder_doc.exists:
            return None # Reminder not found

        reminder_data = reminder_doc.to_dict()

        # Authorize access based on care_profile_id or user_id
        if 'care_profile_id' in reminder_data and reminder_data['care_profile_id']:
             await authorize_care_profile_access(reminder_data['care_profile_id'], current_user)
        elif 'user_id' in reminder_data and reminder_data['user_id'] == current_user.id:
             # Reminder is linked directly to the user
             pass # Authorized
        else:
             # Reminder is not linked to an authorized care profile or the user
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this reminder")

        return reminder_data

    except firestore.exceptions.FirebaseError as e:
        print(f"Firestore error in get_reminder_by_id_internal: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error retrieving reminder: {str(e)}")
    except HTTPException:
        raise # Re-raise HTTPException from authorization
    except Exception as e:
        print(f"Unexpected error in get_reminder_by_id_internal: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")

# Routes (updated to use authentication, authorization, error handling, and server timestamps)
@router.post("/", response_model=ReminderInDB, status_code=status.HTTP_201_CREATED)
async def create_reminder(reminder_create: ReminderCreate, current_user: UserInDB = Depends(get_authenticated_user)):
    try:
        reminder_id = str(uuid.uuid4())

        # Authorize access to the care profile specified in the request if present
        if reminder_create.care_profile_id:
             await authorize_care_profile_access(reminder_create.care_profile_id, current_user)
        elif reminder_create.user_id is not None and reminder_create.user_id != current_user.id:
             # Reminder is linked directly to a user, ensure it's the current user
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot create reminder for another user without a care profile.")
        # If neither care_profile_id nor user_id is provided, or user_id is current_user.id, proceed.
        # If user_id is None, we might default it to current_user.id depending on policy.
        if reminder_create.user_id is None and reminder_create.care_profile_id is None:
             reminder_create.user_id = current_user.id # Default to current user if no care profile specified
        elif reminder_create.user_id is None and reminder_create.care_profile_id is not None:
             # If care_profile_id is present, the user_id in the model refers to the care profile's associated user.
             # This requires fetching the care profile to get the associated user_id.
             # For simplicity in this edit, let's assume the frontend provides the correct user_id (associated with care profile) or it's not needed for authz if care_profile_id is used.
             # A more robust approach would fetch the care profile here and validate/set the user_id.
             pass # Assuming user_id is either provided or not strictly needed if care_profile_id is used for filtering/authz.

        reminder_data_to_store = reminder_create.model_dump(exclude_unset=True)

        # Ensure user_id is explicitly set from authenticated user if not already
        reminder_data_to_store["user_id"] = current_user.id

        # Pydantic models with datetime types and json_encoders should
        # handle conversion to Firestore-compatible formats.

        firestore_data = {
            "id": reminder_id,
            **reminder_data_to_store, # Includes user_id, care_profile_id, type, reminder_time, message, etc.
            "created_at": FieldValue.serverTimestamp(),
            "updated_at": FieldValue.serverTimestamp(),
            "is_active": reminder_data_to_store.get("is_active", True) # Ensure is_active default is handled
        }

        db.collection('reminders').document(reminder_id).set(firestore_data)

        # Retrieve the created document to return as ReminderInDB
        created_reminder_doc = db.collection('reminders').document(reminder_id).get()
        if not created_reminder_doc.exists:
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve reminder after creation.")

        return ReminderInDB(**created_reminder_doc.to_dict())

    except HTTPException as http_exc:
        raise http_exc # Re-raise HTTPException from authorization or bad request
    except firestore.exceptions.FirebaseError as e:
        print(f"Firestore error during reminder creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during reminder creation: {str(e)}"
        )
    except Exception as e:
        print(f"Unexpected error during reminder creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during reminder creation: {str(e)}"
        )

@router.get("/care_profile/{care_profile_id}", response_model=List[ReminderInDB])
async def get_care_profile_reminders(
    care_profile_id: str,
    active_only: Optional[bool] = None,
    reminder_type: Optional[ReminderType] = None,
    current_user: UserInDB = Depends(get_authenticated_user) # Inject authenticated user
):
    try:
        # Authorize access to the care profile
        await authorize_care_profile_access(care_profile_id, current_user)

        query = db.collection('reminders').where("care_profile_id", "==", care_profile_id)

        if active_only is not None:
            query = query.where("is_active", "==", active_only)
        if reminder_type:
            query = query.where("type", "==", reminder_type.value)

        # Order by reminder time
        query = query.order_by("reminder_time")

        reminder_docs = query.stream()
        reminders_list = []
        for doc in reminder_docs:
            rem_data = doc.to_dict()
            # Pydantic model handles conversion from Firestore timestamps/datetimes
            reminders_list.append(ReminderInDB(**rem_data))

        return reminders_list
    except HTTPException as http_exc:
        raise http_exc # Re-raise HTTPException from authorization
    except firestore.exceptions.FirebaseError as e:
        print(f"Firestore error retrieving reminders for care_profile {care_profile_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error retrieving reminders: {str(e)}"
        )
    except Exception as e:
        print(f"Unexpected error retrieving reminders for care_profile {care_profile_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.get("/{reminder_id}", response_model=ReminderInDB)
async def get_reminder(reminder_id: str, current_user: UserInDB = Depends(get_authenticated_user)):
    # Use the helper function which includes authorization
    reminder_obj = await get_reminder_by_id_internal(reminder_id, current_user)
    if not reminder_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found"
        )
    # Authorization check is handled within get_reminder_by_id_internal
    return ReminderInDB(**reminder_obj) # Return as Pydantic model

@router.put("/{reminder_id}", response_model=ReminderInDB)
async def update_reminder(
    reminder_id: str,
    reminder_update: ReminderUpdate,
    current_user: UserInDB = Depends(get_authenticated_user) # Inject authenticated user
):
    try:
        reminder_ref = db.collection('reminders').document(reminder_id)

        # Use the helper function to get the existing reminder and perform authorization check
        existing_rem_doc = await get_reminder_by_id_internal(reminder_id, current_user)

        if not existing_rem_doc:
            # Helper raises 403 if unauthorized, so 404 means not found or not accessible
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reminder not found"
            )

        # Authorization check is handled by get_reminder_by_id_internal.

        update_data_dict = reminder_update.model_dump(exclude_unset=True)

        if not update_data_dict:
             return ReminderInDB(**existing_rem_doc) # Return current reminder if no fields provided for update

        # Use server timestamp for updated_at
        update_data_dict["updated_at"] = FieldValue.serverTimestamp()

        reminder_ref.update(update_data_dict)

        # Get updated reminder from Firestore to return in response
        updated_reminder_doc = reminder_ref.get()
        if not updated_reminder_doc.exists:
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve reminder after update.")

        return ReminderInDB(**updated_reminder_doc.to_dict())

    except HTTPException as http_exc:
        raise http_exc # Re-raise HTTPException from authorization or not found
    except firestore.exceptions.FirebaseError as e:
        print(f"Firestore error during reminder update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during reminder update: {str(e)}"
        )
    except Exception as e:
        print(f"Unexpected error during reminder update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during reminder update"
        )

@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reminder(
    reminder_id: str,
    current_user: UserInDB = Depends(get_authenticated_user) # Inject authenticated user
):
    try:
        reminder_ref = db.collection('reminders').document(reminder_id)

        # Use the helper function to get the existing reminder and perform authorization check
        existing_rem_doc = await get_reminder_by_id_internal(reminder_id, current_user)

        if not existing_rem_doc:
            # Helper raises 403 if unauthorized, so 404 means not found or not accessible
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reminder not found"
            )

        # Authorization check is handled by get_reminder_by_id_internal.

        reminder_ref.delete()
        return # Return None for 204 No Content

    except HTTPException as http_exc:
        raise http_exc # Re-raise HTTPException from authorization or not found
    except firestore.exceptions.FirebaseError as e:
        print(f"Firestore error during reminder deletion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during reminder deletion: {str(e)}"
        )
    except Exception as e:
        print(f"Unexpected error during reminder deletion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during reminder deletion"
        )