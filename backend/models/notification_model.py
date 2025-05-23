from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class NotificationType(str, Enum):
    APPOINTMENT_REMINDER = "appointment_reminder"
    MEDICATION_REMINDER = "medication_reminder"
    HEALTH_ALERT = "health_alert"
    NEW_MESSAGE = "new_message"
    CARE_TEAM_UPDATE = "care_team_update"
    SUBSCRIPTION_UPDATE = "subscription_update"
    GENERAL_INFORMATION = "general_information"
    EMERGENCY_ALERT = "emergency_alert"
    OTHER = "other"

class NotificationBase(BaseModel):
    user_id: str
    title: str
    body: str
    type: NotificationType
    timestamp: datetime = Field(default_factory=datetime.now)
    is_read: bool = False
    related_item_id: Optional[str] = None # e.g., appointment_id, medication_id
    related_item_type: Optional[str] = None # e.g., 'appointment', 'medication'
    deep_link: Optional[str] = None # For navigation within the app
    data: Optional[Dict[str, Any]] = None # Additional payload
    scheduled_time: Optional[datetime] = None # For scheduled notifications

class NotificationCreate(NotificationBase):
    pass

class NotificationUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    type: Optional[NotificationType] = None
    is_read: Optional[bool] = None
    # Other fields are generally not updated after creation, but can be added if needed

class NotificationInDB(NotificationBase):
    id: str # Document ID from Firestore
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }