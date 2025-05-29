from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from enum import Enum
from datetime import datetime, date, time

# Enum for different types of calendar events
class EventType(str, Enum):
    APPOINTMENT = "appointment"
    MEDICATION = "medication"
    TASK = "task"
    HEALTH_CHECK = "health_check"

# Enum for the status of a calendar event
class EventStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    MISSED = "missed"
    SKIPPED = "skipped"
    TAKEN = "taken"  # Specifically for medication events

# Base model for calendar event data
class CalendarEventBase(BaseModel):
    title: str
    event_type: EventType
    date: date
    time: Optional[time] = None
    status: EventStatus = EventStatus.PENDING
    care_profile_id: str  # Links event to a care profile
    details: Optional[Dict] = None  # Stores event-specific additional information
    color_code: Optional[str] = None  # For color-coding events in the UI
    reminder: Optional[bool] = True  # Indicates if a reminder should be sent
    reminder_time: Optional[int] = 30  # Reminder time in minutes before the event

# Model for creating a new calendar event, inherits from CalendarEventBase
class CalendarEventCreate(CalendarEventBase):
    user_id: str  # ID of the user (caregiver) creating the event

# Model for updating an existing calendar event, all fields are optional
class CalendarEventUpdate(BaseModel):
    title: Optional[str] = None
    event_type: Optional[EventType] = None
    date: Optional[date] = None
    time: Optional[time] = None
    status: Optional[EventStatus] = None
    details: Optional[Dict] = None
    color_code: Optional[str] = None
    reminder: Optional[bool] = None
    reminder_time: Optional[int] = None

# Model representing a calendar event in the database, includes ID and timestamps
class CalendarEventInDB(CalendarEventBase):
    id: str
    user_id: str  # ID of the user (caregiver) who created the event
    created_at: datetime
    updated_at: datetime

# Represents a single day in the calendar, containing a list of its events
class CalendarDay(BaseModel):
    date: date
    events: List[CalendarEventInDB] = []

# Represents a full month in the calendar, with events organized by day
class CalendarMonth(BaseModel):
    year: int
    month: int  # Month number (1-12)
    days: Dict[str, CalendarDay] = {}  # Dictionary mapping day string to CalendarDay object

# Helper function to get a default color based on event type
def get_event_color(event_type: EventType) -> str:
    colors = {
        EventType.APPOINTMENT: "#8A7FE0",  # Purple for appointments
        EventType.MEDICATION: "#00A3B4",  # Teal for medications
        EventType.TASK: "#FF6B6B",  # Red for tasks
        EventType.HEALTH_CHECK: "#4CAF50"  # Green for health checks
    }
    return colors.get(event_type, "#8A7FE0")

# Helper function to create a CalendarEvent from appointment data
def create_calendar_event_from_appointment(appointment_id: str, appointment_data: dict) -> CalendarEventCreate:
    return CalendarEventCreate(
        title=f"Appointment ({appointment_data.get('doctor_name', 'Doc')})",
        event_type=EventType.APPOINTMENT,
        date=date.fromisoformat(appointment_data.get('date')) if appointment_data.get('date') else None,
        time=time.fromisoformat(appointment_data.get('time')) if appointment_data.get('time') else None,
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

# Helper function to create a CalendarEvent from medication data and a specific dose time
def create_calendar_event_from_medication(medication_id: str, medication_data: dict, dose_time: str) -> CalendarEventCreate:
    return CalendarEventCreate(
        title=medication_data.get('name', 'Medication'),
        event_type=EventType.MEDICATION,
        date=date.today(),
        time=time.fromisoformat(dose_time),
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