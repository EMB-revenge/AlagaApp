from fastapi import APIRouter, HTTPException, Depends, Body
from typing import List, Optional
from firebase_admin import firestore
from google.cloud.firestore import FieldValue

# Import models from the models directory
from ..models.care_profile import CareProfileBase, CareProfileCreate, CareProfileUpdate, CareProfileInDB
from ..models.user_model import UserInDB

# Import authentication dependency
from .users import get_authenticated_user

# Use globally initialized Firestore client
from ..main import db

router = APIRouter(
    prefix="/care_profiles",
    tags=["care_profiles"],
    responses={404: {"description": "Not found"}},
)

CARE_PROFILES_COLLECTION = "care_profiles"

# Helper function to get a care profile by ID with authorization check
async def get_care_profile_by_id_authorized(profile_id: str, current_user: UserInDB) -> Optional[CareProfileInDB]:
    """Get a care profile by ID and check if the current user is authorized to access it."""
    try:
        doc_ref = db.collection(CARE_PROFILES_COLLECTION).document(profile_id)
        doc = await doc_ref.get()
        if not doc.exists:
            return None # Care profile not found
        
        profile_data = {**doc.to_dict(), "id": doc.id}
        
        # Authorization check: Ensure the current user created this care profile
        if profile_data.get('user_id') != current_user.id:
             raise HTTPException(status_code=403, detail="Not authorized to access this care profile")

        # Pydantic model will handle conversion from Firestore timestamps/dates
        return CareProfileInDB(**profile_data)

    except firestore.exceptions.FirebaseError as e:
        print(f"Firestore error in get_care_profile_by_id_authorized for profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Database error retrieving care profile: {str(e)}")
    except HTTPException:
        raise # Re-raise HTTPException from authorization
    except Exception as e:
        print(f"Unexpected error in get_care_profile_by_id_authorized: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

# --- CRUD Endpoints for Care Profiles (updated for authentication and authorization) ---

@router.post("/", response_model=CareProfileInDB, status_code=201)
async def create_care_profile(
    profile_data: CareProfileCreate = Body(...),
    current_user: UserInDB = Depends(get_authenticated_user)
):
    """
    Create a new care profile for the authenticated user (caregiver).
    The caregiver's user ID is taken from the authenticated user.
    """
    try:
        profile_dict = profile_data.model_dump(exclude_unset=True)
        
        # Set user_id (caregiver_id) from the authenticated user
        profile_dict['user_id'] = current_user.id

        # Use server timestamps
        profile_dict['created_at'] = FieldValue.serverTimestamp()
        profile_dict['updated_at'] = FieldValue.serverTimestamp()

        # Let Firestore generate a unique ID for the care profile document
        doc_ref = db.collection(CARE_PROFILES_COLLECTION).document()
        await doc_ref.set(profile_dict)
        
        # Retrieve the created document to return as CareProfileInDB
        created_profile_doc = await doc_ref.get()
        if not created_profile_doc.exists:
             raise HTTPException(status_code=500, detail="Failed to retrieve care profile after creation.")

        created_profile_data = {**created_profile_doc.to_dict(), "id": created_profile_doc.id}
        return CareProfileInDB(**created_profile_data)

    except firestore.exceptions.FirebaseError as e:
        print(f"Firestore error during care profile creation for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Database error creating care profile: {str(e)}")
    except Exception as e:
        print(f"Unexpected error during care profile creation: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@router.get("/{profile_id}", response_model=CareProfileInDB)
async def get_care_profile_by_id(
    profile_id: str,
    current_user: UserInDB = Depends(get_authenticated_user)
):
    """
    Get a specific care profile by its unique ID, with authorization check.
    """
    # Authorization check is handled within get_care_profile_by_id_authorized helper
    profile = await get_care_profile_by_id_authorized(profile_id, current_user)
    
    if not profile:
         raise HTTPException(status_code=404, detail=f"Care profile not found with ID: {profile_id}")

    return profile

@router.put("/{profile_id}", response_model=CareProfileInDB)
async def update_care_profile(
    profile_id: str,
    profile_update_data: CareProfileUpdate = Body(...),
    current_user: UserInDB = Depends(get_authenticated_user)
):
    """
    Update an existing care profile by its unique ID, with authorization check.
    """
    try:
        doc_ref = db.collection(CARE_PROFILES_COLLECTION).document(profile_id)
        
        # Authorization check using the helper
        existing_profile = await get_care_profile_by_id_authorized(profile_id, current_user)
        if not existing_profile:
            # Helper raises 403 if unauthorized, so 404 means not found or not accessible
            raise HTTPException(status_code=404, detail=f"Care profile not found with ID: {profile_id} to update")

        update_data = profile_update_data.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields provided for update")

        # Use server timestamp
        update_data['updated_at'] = FieldValue.serverTimestamp()

        await doc_ref.update(update_data)
        
        updated_doc = await doc_ref.get()
        if not updated_doc.exists:
             raise HTTPException(status_code=500, detail="Failed to retrieve care profile after update.")

        updated_profile_data = {**updated_doc.to_dict(), "id": updated_doc.id}
        return CareProfileInDB(**updated_profile_data)

    except HTTPException as http_exc:
        raise http_exc # Re-raise HTTPException from authorization or not found
    except firestore.exceptions.FirebaseError as e:
        print(f"Firestore error during care profile update for profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Database error updating care profile: {str(e)}")
    except Exception as e:
        print(f"Unexpected error during care profile update: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@router.delete("/{profile_id}", status_code=204)
async def delete_care_profile(
    profile_id: str,
    current_user: UserInDB = Depends(get_authenticated_user)
):
    """
    Delete a care profile by its unique ID, with authorization check.
    """
    try:
        doc_ref = db.collection(CARE_PROFILES_COLLECTION).document(profile_id)
        
        # Authorization check using the helper
        existing_profile = await get_care_profile_by_id_authorized(profile_id, current_user)
        if not existing_profile:
            # Helper raises 403 if unauthorized, so 404 means not found or not accessible
            raise HTTPException(status_code=404, detail=f"Care profile not found with ID: {profile_id} to delete")
        
        await doc_ref.delete()
        return # No content to return for 204

    except HTTPException as http_exc:
        raise http_exc # Re-raise HTTPException from authorization or not found
    except firestore.exceptions.FirebaseError as e:
        print(f"Firestore error during care profile deletion for profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Database error deleting care profile: {str(e)}")
    except Exception as e:
        print(f"Unexpected error during care profile deletion: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@router.get("/user/me", response_model=List[CareProfileInDB])
async def list_care_profiles_for_user(
    limit: int = 10,
    current_user: UserInDB = Depends(get_authenticated_user)
):
    """
    List all care profiles created by the authenticated user (caregiver).
    """
    try:
        # Query profiles where user_id matches the authenticated user's ID
        profiles_query = db.collection(CARE_PROFILES_COLLECTION).where('user_id', '==', current_user.id).limit(limit)
        docs = profiles_query.stream()
        
        profiles_list = []
        # Using async for with stream() for better performance with async endpoints
        async for doc in docs:
            profile_data = {**doc.to_dict(), "id": doc.id}
            # Pydantic model handles conversion from Firestore timestamps/dates
            profiles_list.append(CareProfileInDB(**profile_data))
        
        return profiles_list

    except firestore.exceptions.FirebaseError as e:
        print(f"Firestore error listing care profiles for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Database error listing care profiles: {str(e)}")
    except Exception as e:
        print(f"Unexpected error listing care profiles: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")