from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

# Enum for different types of notifications
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

# Base model for notification data
class NotificationBase(BaseModel):
    user_id: str
    title: str
    body: str
    type: NotificationType
    timestamp: datetime = Field(default_factory=datetime.now) # Timestamp of notification creation
    is_read: bool = False # Whether the notification has been read
    related_item_id: Optional[str] = None # ID of a related item (e.g., appointment, medication)
    related_item_type: Optional[str] = None # Type of the related item
    deep_link: Optional[str] = None # Link for in-app navigation
    data: Optional[Dict[str, Any]] = None # Additional data payload for the notification
    scheduled_time: Optional[datetime] = None # Time for a scheduled notification

# Model for creating a new notification, inherits from NotificationBase
class NotificationCreate(NotificationBase):
    pass

# Model for updating an existing notification, for read status
class NotificationUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    type: Optional[NotificationType] = None
    is_read: Optional[bool] = None
    # Typically only 'is_read' is updated, other fields can be added if needed

# Model representing a notification in the database, includes ID and timestamps
class NotificationInDB(NotificationBase):
    id: str # Firestore document ID
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat() # Custom encoder for datetime objects
        }