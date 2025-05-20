from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Body
from firebase_admin import firestore
import datetime

# Import models from the models directory
from ..models.care_profile import CareProfileBase, CareProfileCreate, CareProfileUpdate, CareProfileInDB

router = APIRouter()

# Firestore client
db = firestore.client()
CARE_PROFILES_COLLECTION = "care_profiles"

# --- CRUD Endpoints for Care Profiles ---

@router.post("/care_profiles/user/{user_id}", response_model=CareProfileInDB, status_code=201)
async def create_care_profile_for_user(user_id: str, profile_data: CareProfileCreate = Body(...)):
    """
    Create a new care profile for a specific user (caregiver).
    The `user_id` in the path is the ID of the caregiver creating the profile.
    """
    try:
        profile_dict = profile_data.dict()
        # Add user_id (caregiver_id) and timestamps
        timestamp = datetime.datetime.utcnow().isoformat()
        profile_dict['user_id'] = user_id
        profile_dict['created_at'] = timestamp
        profile_dict['updated_at'] = timestamp

        # Let Firestore generate a unique ID for the care profile document
        doc_ref = db.collection(CARE_PROFILES_COLLECTION).document()
        await doc_ref.set(profile_dict)
        
        created_profile_data = {**profile_dict, "id": doc_ref.id}
        return CareProfileInDB(**created_profile_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating care profile: {e}")

@router.get("/care_profiles/{profile_id}", response_model=CareProfileInDB)
async def get_care_profile_by_id(profile_id: str):
    """
    Get a specific care profile by its unique ID.
    """
    try:
        doc_ref = db.collection(CARE_PROFILES_COLLECTION).document(profile_id)
        doc = await doc_ref.get()
        if doc.exists:
            profile_data = {**doc.to_dict(), "id": doc.id}
            return CareProfileInDB(**profile_data)
        else:
            raise HTTPException(status_code=404, detail=f"Care profile not found with ID: {profile_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving care profile: {e}")

@router.put("/care_profiles/{profile_id}", response_model=CareProfileInDB)
async def update_care_profile(profile_id: str, profile_update_data: CareProfileUpdate = Body(...)):
    """
    Update an existing care profile by its unique ID.
    """
    try:
        doc_ref = db.collection(CARE_PROFILES_COLLECTION).document(profile_id)
        doc = await doc_ref.get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail=f"Care profile not found with ID: {profile_id} to update")

        update_data = profile_update_data.dict(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields provided for update")

        update_data['updated_at'] = datetime.datetime.utcnow().isoformat()
        await doc_ref.update(update_data)
        
        updated_doc = await doc_ref.get()
        updated_profile_data = {**updated_doc.to_dict(), "id": updated_doc.id}
        return CareProfileInDB(**updated_profile_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating care profile: {e}")

@router.delete("/care_profiles/{profile_id}", status_code=204)
async def delete_care_profile(profile_id: str):
    """
    Delete a care profile by its unique ID.
    """
    try:
        doc_ref = db.collection(CARE_PROFILES_COLLECTION).document(profile_id)
        doc = await doc_ref.get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail=f"Care profile not found with ID: {profile_id} to delete")
        
        await doc_ref.delete()
        return # No content to return for 204
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting care profile: {e}")

@router.get("/care_profiles/user/{user_id}", response_model=List[CareProfileInDB])
async def list_care_profiles_for_user(user_id: str, limit: int = 10):
    """
    List all care profiles created by a specific user (caregiver).
    """
    try:
        profiles_query = db.collection(CARE_PROFILES_COLLECTION).where('user_id', '==', user_id).limit(limit)
        docs = await profiles_query.stream()
        profiles_list = []
        async for doc in docs:
            profile_data = {**doc.to_dict(), "id": doc.id}
            profiles_list.append(CareProfileInDB(**profile_data))
        return profiles_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing care profiles: {e}")