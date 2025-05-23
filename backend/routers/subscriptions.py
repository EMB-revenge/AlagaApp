from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime, timedelta
import firebase_admin
# Use globally initialized Firestore client
from ..main import db
from pydantic import BaseModel

# Import models
# sys.path.append("..") # Remove unnecessary sys.path modification
from ..models.subscription import (
    SubscriptionTier, 
    SubscriptionFeatures, 
    SubscriptionBase, 
    SubscriptionCreate, 
    SubscriptionUpdate, 
    SubscriptionInDB,
    get_default_features
)

# Fix import error # Remove unnecessary comment
# import sys # Remove unnecessary sys import
# sys.path.append("..") # Remove unnecessary sys.path modification
from .users import get_authenticated_user # Use get_authenticated_user
from ..models.user_model import UserInDB # Import UserInDB

# Import FieldValue for server timestamps
from google.cloud.firestore import FieldValue

router = APIRouter(
    prefix="/subscriptions",
    tags=["subscriptions"],
    responses={404: {"description": "Not found"}},
)

# Helper functions
# Made async and added error handling and authorization check
async def get_subscription_by_user_id_authorized(user_id: str, current_user: UserInDB) -> Optional[SubscriptionInDB]:
    """Get a subscription by user ID and check if it belongs to the current user"""
    # Authorization check: Ensure the requested user_id matches the authenticated user's ID
    if user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access subscriptions for this user")

    try:
        # Use globally initialized db client
        subscription_ref = db.collection("subscriptions").where("user_id", "==", user_id).limit(1).get()
        
        # Use await for async get()
        subscription_docs = await subscription_ref
        
        if not subscription_docs:
            return None
        
        # Assuming there's only one subscription per user due to limit(1)
        subscription_data = subscription_docs[0].to_dict()
        subscription_data["id"] = subscription_docs[0].id
        
        # Pydantic model will handle conversion from Firestore timestamps/dates
        return SubscriptionInDB(**subscription_data)
    
    except firestore.exceptions.FirebaseError as e:
        print(f"Firestore error in get_subscription_by_user_id_authorized: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error retrieving subscription: {str(e)}")
    except HTTPException:
        raise # Re-raise HTTPException from authorization
    except Exception as e:
        print(f"Unexpected error in get_subscription_by_user_id_authorized: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")

# Routes
@router.post("/", response_model=SubscriptionInDB, status_code=status.HTTP_201_CREATED)
async def create_subscription(subscription: SubscriptionCreate, current_user: UserInDB = Depends(get_authenticated_user)):
    """Create a new subscription for the current user"""
    # Check if the subscription being created is for the authenticated user
    if subscription.user_id != current_user.id:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot create subscription for another user")

    try:
        # Check if user already has a subscription using the authorized helper
        existing_subscription = await get_subscription_by_user_id_authorized(current_user.id, current_user) # Pass current_user
        if existing_subscription:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already has an active subscription"
            )
    
        # Set default features based on tier if not provided
        if not subscription.features:
            subscription.features = get_default_features(subscription.tier)
    
        # Convert Pydantic model to dict for Firestore, handling date and nested features
        subscription_data_to_store = subscription.model_dump(exclude_unset=True)

        # Use server timestamps for created_at and updated_at
        firestore_data = {
            **subscription_data_to_store, # Includes user_id, tier, features, dates, etc.
            "created_at": FieldValue.serverTimestamp(),
            "updated_at": FieldValue.serverTimestamp()
        }
    
        # Save to Firestore with a generated ID
        subscription_ref = db.collection("subscriptions").document()
        await subscription_ref.set(firestore_data) # Use await
    
        # Retrieve the created document to return
        # Use the authorized helper to retrieve and authorize the newly created document
        created_subscription = await get_subscription_by_user_id_authorized(current_user.id, current_user) # Pass current_user
        if not created_subscription:
             # This is an unexpected error if set() was successful and authz passes
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve subscription after creation.")

        return created_subscription

    except HTTPException as http_exc:
        raise http_exc # Re-raise HTTPException from authorization or bad request
    except firestore.exceptions.FirebaseError as e:
        print(f"Firestore error during subscription creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during subscription creation: {str(e)}"
        )
    except Exception as e:
        print(f"Unexpected error during subscription creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.get("/me", response_model=SubscriptionInDB)
async def get_my_subscription(current_user: UserInDB = Depends(get_authenticated_user)):
    """Get the current user's subscription"""
    # Authorization check is handled within the helper
    subscription = await get_subscription_by_user_id_authorized(current_user.id, current_user) # Use authorized helper
    
    # If no subscription exists, create a free tier subscription
    # Note: This automatic creation might be better handled by a separate user creation flow
    # or a dedicated endpoint if subscription is optional. For this edit, keeping the existing logic.
    if not subscription:
        # Create a default free subscription for the current user
        subscription_create = SubscriptionCreate(
            user_id=current_user.id, # Ensure user_id is set correctly
            tier=SubscriptionTier.FREE,
            features=get_default_features(SubscriptionTier.FREE)
        )
        # Call the create_subscription endpoint logic to handle creation and return
        # Avoid calling the function directly to ensure full endpoint logic is applied (e.g., error handling)
        # This requires passing a Body-like object and Depends, which is complex. Replicating logic here for simplicity.
        
        try:
            # Convert Pydantic model to dict for Firestore
            subscription_data_to_store = subscription_create.model_dump(exclude_unset=True)

            # Use server timestamps
            firestore_data = {
                **subscription_data_to_store,
                "created_at": FieldValue.serverTimestamp(),
                "updated_at": FieldValue.serverTimestamp()
            }
        
            subscription_ref = db.collection("subscriptions").document()
            await subscription_ref.set(firestore_data) # Use await

            # Retrieve the created document to return
            created_subscription = await get_subscription_by_user_id_authorized(current_user.id, current_user) # Use authorized helper
            if not created_subscription:
                 raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve auto-created free subscription.")

            return created_subscription

        except firestore.exceptions.FirebaseError as e:
            print(f"Firestore error during auto-creation of free subscription: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error during auto-creation of free subscription: {str(e)}"
            )
        except Exception as e:
             print(f"Unexpected error during auto-creation of free subscription: {e}")
             raise HTTPException(
                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                 detail=f"An unexpected error occurred during auto-creation of free subscription: {str(e)}"
             )
    
    return subscription

@router.put("/me", response_model=SubscriptionInDB)
async def update_my_subscription(subscription_update: SubscriptionUpdate, current_user: UserInDB = Depends(get_authenticated_user)):
    """Update the current user's subscription"""
    try:
        # Get current subscription using the authorized helper
        current_subscription = await get_subscription_by_user_id_authorized(current_user.id, current_user) # Use authorized helper
        if not current_subscription:
            # If the helper returns None, it means no subscription was found for the user
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found for the current user"
            )
    
        # Update subscription data
        update_data = subscription_update.model_dump(exclude_unset=True)
        
        if not update_data:
             return current_subscription # Return current subscription if no updates provided

        # If upgrading to premium, set end date to 30 days from now and set is_active to True
        # Also update features if tier is explicitly changed to PREMIUM
        if "tier" in update_data and update_data["tier"] == SubscriptionTier.PREMIUM.value: # Use .value for Enum
            # Ensure end_date is a date object if the model uses date
            update_data["end_date"] = (datetime.now() + timedelta(days=30)).date() # Use .date()
            update_data["is_active"] = True
            
            # Update features if tier changed to premium and features were not explicitly provided in update
            if current_subscription.tier != SubscriptionTier.PREMIUM and "features" not in update_data:
                update_data["features"] = get_default_features(SubscriptionTier.PREMIUM).model_dump() # Use model_dump() for nested Pydantic
        elif "tier" in update_data and update_data["tier"] != SubscriptionTier.PREMIUM.value: # Handle downgrade or change to free
            # Decide on policy for end_date and is_active on downgrade
            pass # Keep existing logic or implement specific downgrade logic

        # Use server timestamp for updated_at
        update_data["updated_at"] = FieldValue.serverTimestamp()
    
        # Update in Firestore
        subscription_ref = db.collection("subscriptions").document(current_subscription.id)
        await subscription_ref.update(update_data) # Use await
    
        # Get updated subscription using the authorized helper
        updated_subscription = await get_subscription_by_user_id_authorized(current_user.id, current_user) # Use authorized helper
        if not updated_subscription:
             # This is unexpected if update succeeded
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve subscription after update.")

        return updated_subscription

    except HTTPException as http_exc:
        raise http_exc # Re-raise HTTPException from authorization or not found
    except firestore.exceptions.FirebaseError as e:
        print(f"Firestore error during subscription update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during subscription update: {str(e)}"
        )
    except Exception as e:
        print(f"Unexpected error during subscription update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during subscription update: {str(e)}"
        )

@router.post("/upgrade-to-premium", response_model=SubscriptionInDB)
async def upgrade_to_premium(current_user: UserInDB = Depends(get_authenticated_user)):
    """Upgrade the current user's subscription to premium"""
    # This would typically integrate with a payment processor
    # For now, we'll just upgrade the subscription
    
    # Create an update model for premium tier
    subscription_update = SubscriptionUpdate(
        tier=SubscriptionTier.PREMIUM,
        auto_renew=True # Assuming auto_renew is default for premium upgrades
        # Features are set by the update_my_subscription logic if tier changes
    )
    
    # Call the update endpoint logic to handle the update and return
    return await update_my_subscription(subscription_update, current_user)

@router.get("/features", response_model=dict)
async def get_subscription_features():
    """Get the features for each subscription tier"""
    # This endpoint doesn't require authentication as it provides public information
    return {
        SubscriptionTier.FREE.value: get_default_features(SubscriptionTier.FREE).model_dump(), # Use .value and model_dump()
        SubscriptionTier.PREMIUM.value: get_default_features(SubscriptionTier.PREMIUM).model_dump() # Use .value and model_dump()
    }