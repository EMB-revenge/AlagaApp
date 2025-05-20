from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime, timedelta
import firebase_admin
# Use globally initialized Firestore client
from ..main import db
from pydantic import BaseModel

# Import models
sys.path.append("..")
from models.subscription import (
    SubscriptionTier, 
    SubscriptionFeatures, 
    SubscriptionBase, 
    SubscriptionCreate, 
    SubscriptionUpdate, 
    SubscriptionInDB,
    get_default_features
)

# Fix import error
import sys
sys.path.append("..")
from routers.users import get_current_user, UserInDB

router = APIRouter(
    prefix="/subscriptions",
    tags=["subscriptions"],
    responses={404: {"description": "Not found"}},
)

# Helper functions
def get_subscription_by_user_id(user_id: str) -> Optional[SubscriptionInDB]:
    """Get a subscription by user ID"""
    db = firestore.client()
    subscription_ref = db.collection("subscriptions").where("user_id", "==", user_id).limit(1).get()
    
    if not subscription_ref:
        return None
    
    subscription_data = subscription_ref[0].to_dict()
    subscription_data["id"] = subscription_ref[0].id
    return SubscriptionInDB(**subscription_data)

# Routes
@router.post("/", response_model=SubscriptionInDB, status_code=status.HTTP_201_CREATED)
async def create_subscription(subscription: SubscriptionCreate, current_user: UserInDB = Depends(get_current_user)):
    """Create a new subscription for the current user"""
    # Check if user already has a subscription
    existing_subscription = get_subscription_by_user_id(current_user.id)
    if existing_subscription:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has a subscription"
        )
    
    # Set default features based on tier if not provided
    if not subscription.features:
        subscription.features = get_default_features(subscription.tier)
    
    # Set dates
    now = datetime.now().isoformat()
    
    # For premium subscriptions, set end date to 30 days from now
    end_date = None
    if subscription.tier == SubscriptionTier.PREMIUM:
        end_date = (datetime.now() + timedelta(days=30)).isoformat()
    
    # Create subscription document
    subscription_data = {
        "user_id": current_user.id,
        "tier": subscription.tier,
        "features": subscription.features.dict(),
        "start_date": now,
        "end_date": end_date,
        "is_active": True,
        "auto_renew": subscription.auto_renew,
        "created_at": now,
        "updated_at": now
    }
    
    # Save to Firestore
    db = firestore.client()
    subscription_ref = db.collection("subscriptions").document()
    subscription_ref.set(subscription_data)
    
    # Return the created subscription
    return SubscriptionInDB(id=subscription_ref.id, **subscription_data)

@router.get("/me", response_model=SubscriptionInDB)
async def get_my_subscription(current_user: UserInDB = Depends(get_current_user)):
    """Get the current user's subscription"""
    subscription = get_subscription_by_user_id(current_user.id)
    
    # If no subscription exists, create a free tier subscription
    if not subscription:
        # Create a default free subscription
        subscription_create = SubscriptionCreate(
            tier=SubscriptionTier.FREE,
            features=get_default_features(SubscriptionTier.FREE)
        )
        return await create_subscription(subscription_create, current_user)
    
    return subscription

@router.put("/me", response_model=SubscriptionInDB)
async def update_my_subscription(subscription_update: SubscriptionUpdate, current_user: UserInDB = Depends(get_current_user)):
    """Update the current user's subscription"""
    # Get current subscription
    current_subscription = get_subscription_by_user_id(current_user.id)
    if not current_subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    # Update subscription data
    update_data = subscription_update.dict(exclude_unset=True)
    
    # If upgrading to premium, set end date to 30 days from now
    if "tier" in update_data and update_data["tier"] == SubscriptionTier.PREMIUM:
        update_data["end_date"] = (datetime.now() + timedelta(days=30)).isoformat()
        update_data["is_active"] = True
        
        # Update features if tier changed
        if current_subscription.tier != SubscriptionTier.PREMIUM:
            update_data["features"] = get_default_features(SubscriptionTier.PREMIUM).dict()
    
    # Update timestamp
    update_data["updated_at"] = datetime.now().isoformat()
    
    # Update in Firestore
    db = firestore.client()
    subscription_ref = db.collection("subscriptions").document(current_subscription.id)
    subscription_ref.update(update_data)
    
    # Get updated subscription
    updated_subscription = subscription_ref.get().to_dict()
    updated_subscription["id"] = current_subscription.id
    
    return SubscriptionInDB(**updated_subscription)

@router.post("/upgrade-to-premium", response_model=SubscriptionInDB)
async def upgrade_to_premium(current_user: UserInDB = Depends(get_current_user)):
    """Upgrade the current user's subscription to premium"""
    # This would typically integrate with a payment processor
    # For now, we'll just upgrade the subscription
    
    subscription_update = SubscriptionUpdate(
        tier=SubscriptionTier.PREMIUM,
        features=get_default_features(SubscriptionTier.PREMIUM),
        auto_renew=True
    )
    
    return await update_my_subscription(subscription_update, current_user)

@router.get("/features", response_model=dict)
async def get_subscription_features():
    """Get the features for each subscription tier"""
    return {
        "free": get_default_features(SubscriptionTier.FREE).dict(),
        "premium": get_default_features(SubscriptionTier.PREMIUM).dict()
    }