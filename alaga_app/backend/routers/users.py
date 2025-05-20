from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from firebase_admin import auth, firestore
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
import uuid

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

# Firestore client
db = firestore.client()

# Models
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    phone_number: Optional[str] = None
    birth_date: Optional[str] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    birth_date: Optional[str] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    profile_picture_url: Optional[str] = None

class UserInDB(UserBase):
    id: str
    created_at: str
    updated_at: str
    profile_picture_url: Optional[str] = None
    is_caregiver: bool = False
    is_verified: bool = False

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenData(BaseModel):
    token: str
    user_id: str
    email: str

# Helper functions
def get_user_by_id(user_id: str):
    try:
        user_doc = db.collection('users').document(user_id).get()
        if user_doc.exists:
            return user_doc.to_dict()
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Routes
@router.post("/register", response_model=UserInDB, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate):
    try:
        # Check if user already exists
        try:
            existing_user = auth.get_user_by_email(user.email)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        except auth.UserNotFoundError:
            pass
        
        # Create user in Firebase Auth
        user_record = auth.create_user(
            email=user.email,
            password=user.password,
            display_name=user.full_name,
            phone_number=user.phone_number if user.phone_number else None,
        )
        
        # Create user document in Firestore
        current_time = datetime.now().isoformat()
        user_data = {
            "id": user_record.uid,
            "email": user.email,
            "full_name": user.full_name,
            "phone_number": user.phone_number,
            "birth_date": user.birth_date,
            "gender": user.gender,
            "address": user.address,
            "emergency_contact": user.emergency_contact,
            "created_at": current_time,
            "updated_at": current_time,
            "profile_picture_url": None,
            "is_caregiver": False,
            "is_verified": False
        }
        
        db.collection('users').document(user_record.uid).set(user_data)
        
        return user_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )

@router.post("/login", response_model=TokenData)
async def login_user(user_credentials: UserLogin):
    try:
        # This would typically use Firebase Auth REST API
        # For simplicity, we're simulating the token generation
        # In a real app, you would use Firebase Auth REST API or Firebase Admin SDK
        
        # Verify user exists
        try:
            user = auth.get_user_by_email(user_credentials.email)
        except auth.UserNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # In a real implementation, you would verify the password
        # and generate a custom token or use Firebase Auth REST API
        
        # Create a custom token (simulated)
        custom_token = f"simulated_token_{uuid.uuid4()}"
        
        return {
            "token": custom_token,
            "user_id": user.uid,
            "email": user.email
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login error: {str(e)}"
        )

@router.get("/me", response_model=UserInDB)
async def get_current_user(user_id: str):
    # In a real app, you would extract the user_id from the token
    # For simplicity, we're accepting it as a query parameter
    user_data = get_user_by_id(user_id)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user_data

@router.put("/me", response_model=UserInDB)
async def update_user(user_id: str, user_update: UserUpdate):
    try:
        # Get current user data
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update only provided fields
        update_data = {k: v for k, v in user_update.model_dump().items() if v is not None}
        update_data["updated_at"] = datetime.now().isoformat()
        
        # Update in Firestore
        user_ref.update(update_data)
        
        # Get updated user
        updated_user = user_ref.get().to_dict()
        return updated_user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating user: {str(e)}"
        )

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str):
    try:
        # Delete from Firebase Auth
        auth.delete_user(user_id)
        
        # Delete from Firestore
        db.collection('users').document(user_id).delete()
        
        return {"detail": "User deleted successfully"}
    except auth.UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting user: {str(e)}"
        )