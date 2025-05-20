from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from enum import Enum
from datetime import datetime, date

class EventType(str, Enum):
    """Types of events that can be displayed on the calendar"""
    APPOINTMENT = "appointment"
    MEDICATION = "medication"
    TASK = "task"
    HEALTH_CHECK = "health_check"

class EventStatus(str, Enum):
    """Status of calendar events"""
    PENDING = "pending"
    COMPLETED = "completed"
    MISSED = "missed"
    SKIPPED = "skipped"
    TAKEN = "taken"  # For medications

class CalendarEventBase(BaseModel):
    """Base model for calendar events"""
    title: str
    event_type: EventType
    date: str  # ISO format date string (YYYY-MM-DD)
    time: Optional[str] = None  # Time in 24-hour format (HH:MM)
    status: EventStatus = EventStatus.PENDING
    care_profile_id: str  # ID of the care profile this event is for
    details: Optional[Dict] = None  # Additional details specific to event type
    color_code: Optional[str] = None  # Color for visual representation
    reminder: Optional[bool] = True  # Whether to send a reminder
    reminder_time: Optional[int] = 30  # Minutes before event to send reminder

class CalendarEventCreate(CalendarEventBase):
    """Model for creating a new calendar event"""
    pass

class CalendarEventUpdate(BaseModel):
    """Model for updating an existing calendar event"""
    title: Optional[str] = None
    event_type: Optional[EventType] = None
    date: Optional[str] = None
    time: Optional[str] = None
    status: Optional[EventStatus] = None
    details: Optional[Dict] = None
    color_code: Optional[str] = None
    reminder: Optional[bool] = None
    reminder_time: Optional[int] = None

class CalendarEventInDB(CalendarEventBase):
    """Model for a calendar event as stored in the database"""
    id: str
    user_id: str  # ID of the caregiver who created this event
    created_at: str
    updated_at: str

class CalendarDay(BaseModel):
    """Model for a day in the calendar with all events"""
    date: str  # ISO format date string (YYYY-MM-DD)
    events: List[CalendarEventInDB] = []

class CalendarMonth(BaseModel):
    """Model for a month in the calendar"""
    year: int
    month: int  # 1-12
    days: Dict[str, CalendarDay] = {}  # Key is day of month as string

# Helper functions
def get_event_color(event_type: EventType) -> str:
    """Returns the default color for an event type"""
    colors = {
        EventType.APPOINTMENT: "#8A7FE0",  # Purple
        EventType.MEDICATION: "#00A3B4",  # Teal
        EventType.TASK: "#FF6B6B",  # Red
        EventType.HEALTH_CHECK: "#4CAF50"  # Green
    }
    return colors.get(event_type, "#8A7FE0")

def create_calendar_event_from_appointment(appointment_id: str, appointment_data: dict) -> CalendarEventCreate:
    """Creates a calendar event from appointment data"""
    return CalendarEventCreate(
        title=f"Appointment ({appointment_data.get('doctor_name', 'Doc')})",
        event_type=EventType.APPOINTMENT,
        date=appointment_data.get('date'),
        time=appointment_data.get('time'),
        status=EventStatus.PENDING,
        care_profile_id=appointment_data.get('care_profile_id'),
        details={
            "appointment_id": appointment_id,
            "doctor_name": appointment_data.get('doctor_name'),
            "location": appointment_data.get('location'),
            "notes": appointment_data.get('notes')
        },
        color_code=get_event_color(EventType.APPOINTMENT)
    )

def create_calendar_event_from_medication(medication_id: str, medication_data: dict, dose_time: str) -> CalendarEventCreate:
    """Creates a calendar event from medication data"""
    return CalendarEventCreate(
        title=medication_data.get('name', 'Medication'),
        event_type=EventType.MEDICATION,
        date=datetime.now().strftime("%Y-%m-%d"),  # Today's date
        time=dose_time,
        status=EventStatus.PENDING,
        care_profile_id=medication_data.get('care_profile_id'),
        details={
            "medication_id": medication_id,
            "dosage": medication_data.get('dosage'),
            "instructions": medication_data.get('instructions'),
            "frequency": medication_data.get('frequency')
        },
        color_code=get_event_color(EventType.MEDICATION)
    )