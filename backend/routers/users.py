from fastapi import APIRouter, HTTPException, Depends, status, Header
from typing import List, Optional
from firebase_admin import auth, firestore
from pydantic import EmailStr # BaseModel, Field are now in user_model
from datetime import datetime
import uuid
from ..models.user_model import UserBase, UserCreate, UserUpdate, UserInDB # UserFirestore might be more accurate for Firestore interactions
from pydantic import BaseModel # Keep BaseModel for UserLogin and TokenData if not moved

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

# Use globally initialized Firestore client
from ..db import db # Import db from the new db.py file

# Import FieldValue for server timestamps
from google.cloud.firestore import FieldValue

# Models specific to router if not in user_model
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Remove TokenData as backend won't generate tokens this way
# class TokenData(BaseModel):
#     token: str
#     user_id: str
#     email: str

# Dependency to get the authenticated user
async def get_authenticated_user(id_token: str = Header(None)) -> UserInDB:
    if not id_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization: Bearer token header missing"
        )
    
    try:
        # Verify the ID token while checking if the set revocation check was requested.
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        
        # Fetch user from Firestore based on UID
        user_doc = db.collection('users').document(uid).get()
        
        if not user_doc.exists:
            # This case should ideally not happen if a user is in Auth but not Firestore
            # but it's a safeguard.
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User document not found in database"
            )
            
        user_data = user_doc.to_dict()
        
        # Ensure all fields required by UserInDB are present or have defaults
        # Pydantic model should handle datetime conversion from Firestore timestamps
        return UserInDB(**user_data)

    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Firebase ID token"
        )
    except auth.ExpiredIdTokenError:
         raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firebase ID token has expired"
        )
    except auth.RevokedIdTokenError:
         raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firebase ID token has been revoked"
        )
    except auth.CertificateFetchError:
         raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching Firebase public keys"
        )
    except firestore.exceptions.NotFound:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User document not found in database after authentication"
        )
    except Exception as e:
        # Catch any other unexpected errors
        print(f"Authentication/Database error: {e}") # Log the error server-side
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during authentication"
        )

# Helper functions (updated to use specific exceptions)
def get_user_by_id(user_id: str):
    try:
        user_doc = db.collection('users').document(user_id).get()
        if user_doc.exists:
            return user_doc.to_dict()
        return None
    except firestore.exceptions.FirebaseError as e:
         print(f"Database error in get_user_by_id: {e}")
         raise HTTPException(status_code=500, detail=f"Database error retrieving user: {str(e)}")
    except Exception as e:
        print(f"Unexpected error in get_user_by_id: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

# Routes
@router.post("/register", response_model=UserInDB, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate):
    try:
        # Check if user already exists in Firebase Auth
        try:
            auth.get_user_by_email(user.email)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        except auth.UserNotFoundError:
            # User doesn't exist in Auth, proceed with creation
            pass

        # Create user in Firebase Auth
        # Note: The password here is handled by Firebase Auth's internal hashing.
        user_record = auth.create_user(
            email=user.email,
            password=user.password,
            display_name=user.full_name,
            phone_number=user.phone_number if user.phone_number else None,
        )

        # Create user document in Firestore
        # Use FieldValue.serverTimestamp() for accurate timestamps
        user_data = user.model_dump(exclude_unset=True)
        user_data.pop('password', None) # Do not store password in Firestore

        firestore_data = {
            "id": user_record.uid,
            "email": user.email,
            "full_name": user.full_name,
            "phone_number": user.phone_number,
            # Birth date, gender, address, emergency_contact are included from user_data
            **user_data,
            "created_at": FieldValue.serverTimestamp(),
            "updated_at": FieldValue.serverTimestamp(),
            "profile_picture_url": None,
            "is_caregiver": False,
            "is_verified": False # Email verification status would be updated later via Firebase Auth flow
        }

        db.collection('users').document(user_record.uid).set(firestore_data)

        # Retrieve the created document to return as UserInDB (timestamps will be datetime objects)
        created_user_doc = db.collection('users').document(user_record.uid).get()
        return UserInDB(**created_user_doc.to_dict())

    except auth.EmailAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    except auth.AuthError as e:
         print(f"Firebase Auth error during registration: {e}")
         raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Firebase Authentication error: {e}"
        )
    except firestore.exceptions.FirebaseError as e:
         print(f"Firestore error during user registration: {e}")
         raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during registration: {e}"
        )
    except Exception as e:
        # Catch any other unexpected errors
        print(f"Unexpected error during registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during registration"
        )

@router.post("/login", response_model=dict) # Change response model to dict as we don't return TokenData
async def login_user(user_credentials: UserLogin):
    # In a real application using Firebase Authentication, the frontend
    # would handle the login process using a Firebase client SDK (e.g., in Flutter).
    # The frontend would then receive an ID token upon successful authentication.
    # This backend assumes the frontend sends that ID token for authenticated requests.
    # The logic below is NOT a complete backend login endpoint for Firebase Auth.
    # It merely demonstrates where you might have a login endpoint if you were
    # using a different auth system or generating custom tokens (less common).
    # For this project with Firebase Auth, the frontend handles login.

    # The frontend Flutter app should call Firebase Auth SDK's signInWithEmailAndPassword
    # and then send the resulting ID token in the 'Authorization: Bearer <token>'
    # header for protected endpoints like /users/me.

    # This endpoint could potentially be used to verify credentials and return
    # a custom token if needed, but verifying the ID token on subsequent requests
    # is the standard approach.

    # Example of checking if user exists (part of a potential login flow, but not the full secure process):
    try:
        user = auth.get_user_by_email(user_credentials.email)
        # Password verification would happen here if not using Firebase Auth directly for login
        # e.g., using auth.signInWithEmailAndPassword in the frontend

        # If using custom tokens: custom_token = auth.create_custom_token(user.uid)
        # return {"custom_token": custom_token.decode()}

        # As we are relying on frontend Firebase Auth login,
        # this endpoint is effectively just a confirmation that the email exists.
        # The frontend gets the ID token directly from Firebase after login.
        return {"message": "User exists. Frontend should use Firebase Auth to login and obtain ID token.", "user_id": user.uid}

    except auth.UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials or user not found"
        )
    except Exception as e:
        print(f"Login endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during login: {e}"
        )

# Update /me endpoint to use the authentication dependency
@router.get("/me", response_model=UserInDB)
async def get_current_user(current_user: UserInDB = Depends(get_authenticated_user)):
    # The authenticated user object is provided by the dependency
    # No need to fetch user data again here as it's already in current_user
    return current_user

# Update /me PUT endpoint to use the authentication dependency
@router.put("/me", response_model=UserInDB)
async def update_user(user_update: UserUpdate, current_user: UserInDB = Depends(get_authenticated_user)):
    try:
        # Use the authenticated user's ID
        user_ref = db.collection('users').document(current_user.id)
        
        # Get existing data to merge updates
        user_doc = user_ref.get()
        if not user_doc.exists:
             # This should ideally not happen if get_authenticated_user succeeded
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User document not found for authenticated user.")

        # Prepare update data, excluding unset fields and sensitive info
        update_data = user_update.model_dump(exclude_unset=True)
        
        # Use server timestamp for updated_at
        update_data["updated_at"] = FieldValue.serverTimestamp()
        
        if not update_data:
             # Optional: return current user data or a message if no fields provided for update
             return current_user # Return current user data if no updates were provided

        # Update in Firestore using .update() for partial updates
        user_ref.update(update_data)
        
        # Get updated user data from Firestore to return in response
        updated_user_doc = user_ref.get()
        return UserInDB(**updated_user_doc.to_dict())

    except firestore.exceptions.NotFound:
        # Should not happen if auth dependency works, but good safeguard
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Authenticated user document not found"
        )
    except firestore.exceptions.FirebaseError as e:
         print(f"Firestore error during user update: {e}")
         raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during user update: {e}"
        )
    except Exception as e:
        # Catch any other unexpected errors
        print(f"Unexpected error during user update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during user update"
        )

# Update /me DELETE endpoint to use the authentication dependency
@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(current_user: UserInDB = Depends(get_authenticated_user)):
    try:
        # Delete from Firebase Auth using the authenticated user's UID
        auth.delete_user(current_user.id)
        
        # Delete user document from Firestore
        db.collection('users').document(current_user.id).delete()
        
        # Note: HTTP 204 response typically has no body. Returning detail is for clarity during development.
        # In a real app, you might just return a status code or a minimal JSON.
        return {"detail": "User deleted successfully"}

    except auth.UserNotFoundError:
         # Should not happen if auth dependency works, but good safeguard
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Authenticated user not found in Firebase Auth"
        )
    except firestore.exceptions.NotFound:
         # Should not happen if auth dependency works, but good safeguard
         print(f"Firestore document not found for user {current_user.id} during deletion, but Auth user existed.")
         pass # Continue if Auth user was deleted, even if Firestore doc was missing
    except auth.AuthError as e:
         print(f"Firebase Auth error during user deletion: {e}")
         raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Firebase Authentication error during deletion: {e}"
        )
    except firestore.exceptions.FirebaseError as e:
         print(f"Firestore error during user deletion: {e}")
         # Decide whether to raise HTTPException or just log, depending on desired behavior
         # if Auth deletion succeeded but Firestore failed.
         pass # Allow deletion to proceed if Auth deletion was successful
    except Exception as e:
        # Catch any other unexpected errors
        print(f"Unexpected error during user deletion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during user deletion"
        )