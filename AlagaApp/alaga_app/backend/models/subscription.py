from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

class SubscriptionTier(str, Enum):
    """Enum for subscription tiers"""
    FREE = "free"
    PREMIUM = "premium"

class SubscriptionFeatures(BaseModel):
    """Model for subscription features"""
    max_care_profiles: int
    max_tasks_per_day: int
    max_pill_reminders_per_day: int
    can_record_multiple_vitals: bool
    has_enhanced_calendar: bool
    has_smart_reminders: bool

class SubscriptionBase(BaseModel):
    """Base model for user subscriptions"""
    tier: SubscriptionTier = SubscriptionTier.FREE
    features: Optional[SubscriptionFeatures] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_active: bool = True
    auto_renew: bool = False

class SubscriptionCreate(SubscriptionBase):
    """Model for creating a new subscription"""
    pass

class SubscriptionUpdate(BaseModel):
    """Model for updating an existing subscription"""
    tier: Optional[SubscriptionTier] = None
    features: Optional[SubscriptionFeatures] = None
    end_date: Optional[str] = None
    is_active: Optional[bool] = None
    auto_renew: Optional[bool] = None

class SubscriptionInDB(SubscriptionBase):
    """Model for a subscription as stored in the database"""
    id: str
    user_id: str
    created_at: str
    updated_at: str

# Default feature sets based on subscription tier
def get_default_features(tier: SubscriptionTier) -> SubscriptionFeatures:
    """Returns the default features for a given subscription tier"""
    if tier == SubscriptionTier.FREE:
        return SubscriptionFeatures(
            max_care_profiles=1,
            max_tasks_per_day=2,
            max_pill_reminders_per_day=1,
            can_record_multiple_vitals=False,
            has_enhanced_calendar=False,
            has_smart_reminders=False
        )
    elif tier == SubscriptionTier.PREMIUM:
        return SubscriptionFeatures(
            max_care_profiles=5,
            max_tasks_per_day=999,  # Unlimited
            max_pill_reminders_per_day=999,  # Unlimited
            can_record_multiple_vitals=True,
            has_enhanced_calendar=True,
            has_smart_reminders=True
        )
    else:
        raise ValueError(f"Unknown subscription tier: {tier}")