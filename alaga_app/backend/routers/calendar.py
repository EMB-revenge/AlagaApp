from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict
from datetime import datetime, timedelta, date
import calendar as cal
import firebase_admin
from firebase_admin import firestore

# Import models
import sys
sys.path.append("..")
from models.calendar import (
    EventType,
    EventStatus,
    CalendarEventBase,
    CalendarEventCreate,
    CalendarEventUpdate,
    CalendarEventInDB,
    CalendarDay,
    CalendarMonth,
    get_event_color,
    create_calendar_event_from_appointment,
    create_calendar_event_from_medication
)
from routers.users import get_current_user, UserInDB
from models.subscription import SubscriptionTier
from routers.subscriptions import get_subscription_by_user_id

router = APIRouter(
    prefix="/calendar",
    tags=["calendar"],
    responses={404: {"description": "Not found"}},
)

# Helper functions
def get_calendar_event_by_id(event_id: str) -> Optional[CalendarEventInDB]:
    """Get a calendar event by ID"""
    db = firestore.client()
    event_ref = db.collection("calendar_events").document(event_id).get()
    
    if not event_ref.exists:
        return None
    
    event_data = event_ref.to_dict()
    event_data["id"] = event_ref.id
    return CalendarEventInDB(**event_data)

def get_events_by_date_range(user_id: str, care_profile_id: str, start_date: str, end_date: str) -> List[CalendarEventInDB]:
    """Get all events for a user and care profile within a date range"""
    db = firestore.client()
    events_ref = db.collection("calendar_events")\
        .where("user_id", "==", user_id)\
        .where("care_profile_id", "==", care_profile_id)\
        .where("date", ">=", start_date)\
        .where("date", "<=", end_date)\
        .get()
    
    events = []
    for event in events_ref:
        event_data = event.to_dict()
        event_data["id"] = event.id
        events.append(CalendarEventInDB(**event_data))
    
    return events

def get_events_by_date(user_id: str, care_profile_id: str, date_str: str) -> List[CalendarEventInDB]:
    """Get all events for a user and care profile on a specific date"""
    return get_events_by_date_range(user_id, care_profile_id, date_str, date_str)

def check_calendar_access(user_subscription):
    """Check if user has access to enhanced calendar features"""
    has_enhanced_calendar = False
    
    if user_subscription and user_subscription.tier == SubscriptionTier.PREMIUM:
        has_enhanced_calendar = True
    
    return has_enhanced_calendar

# Routes
@router.post("/events", response_model=CalendarEventInDB, status_code=status.HTTP_201_CREATED)
async def create_calendar_event(event: CalendarEventCreate, current_user: UserInDB = Depends(get_current_user)):
    """Create a new calendar event"""
    # Check subscription for enhanced calendar features
    user_subscription = get_subscription_by_user_id(current_user.id)
    has_enhanced_calendar = check_calendar_access(user_subscription)
    
    # Set dates
    now = datetime.now().isoformat()
    
    # Create event document
    event_data = event.dict()
    event_data["user_id"] = current_user.id
    event_data["created_at"] = now
    event_data["updated_at"] = now
    
    # Save to Firestore
    db = firestore.client()
    event_ref = db.collection("calendar_events").document()
    event_ref.set(event_data)
    
    # Return the created event
    return CalendarEventInDB(id=event_ref.id, **event_data)

@router.get("/events/{event_id}", response_model=CalendarEventInDB)
async def get_calendar_event(event_id: str, current_user: UserInDB = Depends(get_current_user)):
    """Get a calendar event by ID"""
    event = get_calendar_event_by_id(event_id)
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Check if event belongs to current user
    if event.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this event"
        )
    
    return event

@router.put("/events/{event_id}", response_model=CalendarEventInDB)
async def update_calendar_event(event_id: str, event_update: CalendarEventUpdate, current_user: UserInDB = Depends(get_current_user)):
    """Update a calendar event"""
    event = get_calendar_event_by_id(event_id)
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Check if event belongs to current user
    if event.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this event"
        )
    
    # Update event data
    update_data = event_update.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.now().isoformat()
    
    # Update in Firestore
    db = firestore.client()
    event_ref = db.collection("calendar_events").document(event_id)
    event_ref.update(update_data)
    
    # Get updated event
    updated_event = event_ref.get().to_dict()
    updated_event["id"] = event_id
    
    return CalendarEventInDB(**updated_event)

@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_calendar_event(event_id: str, current_user: UserInDB = Depends(get_current_user)):
    """Delete a calendar event"""
    event = get_calendar_event_by_id(event_id)
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Check if event belongs to current user
    if event.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this event"
        )
    
    # Delete from Firestore
    db = firestore.client()
    db.collection("calendar_events").document(event_id).delete()
    
    return None

@router.get("/events/day/{date}", response_model=CalendarDay)
async def get_day_events(
    date: str,
    care_profile_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Get all events for a specific day"""
    events = get_events_by_date(current_user.id, care_profile_id, date)
    
    return CalendarDay(
        date=date,
        events=events
    )

@router.get("/events/month/{year}/{month}", response_model=CalendarMonth)
async def get_month_events(
    year: int,
    month: int,
    care_profile_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Get all events for a specific month"""
    # Check subscription for enhanced calendar features
    user_subscription = get_subscription_by_user_id(current_user.id)
    has_enhanced_calendar = check_calendar_access(user_subscription)
    
    # Calculate start and end dates for the month
    _, last_day = cal.monthrange(year, month)
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-{last_day:02d}"
    
    # Get all events for the month
    events = get_events_by_date_range(current_user.id, care_profile_id, start_date, end_date)
    
    # Organize events by day
    days = {}
    for day in range(1, last_day + 1):
        day_str = f"{year}-{month:02d}-{day:02d}"
        days[str(day)] = CalendarDay(date=day_str, events=[])
    
    # Add events to their respective days
    for event in events:
        day = int(event.date.split('-')[2])
        if str(day) in days:
            days[str(day)].events.append(event)
    
    return CalendarMonth(
        year=year,
        month=month,
        days=days
    )

@router.get("/events/today", response_model=CalendarDay)
async def get_today_events(
    care_profile_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Get all events for today"""
    today = datetime.now().strftime("%Y-%m-%d")
    return await get_day_events(today, care_profile_id, current_user)

@router.post("/events/mark-status/{event_id}", response_model=CalendarEventInDB)
async def mark_event_status(
    event_id: str,
    status: EventStatus,
    current_user: UserInDB = Depends(get_current_user)
):
    """Mark an event as completed, missed, skipped, or taken"""
    event = get_calendar_event_by_id(event_id)
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Check if event belongs to current user
    if event.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this event"
        )
    
    # Update event status
    update_data = {"status": status, "updated_at": datetime.now().isoformat()}
    
    # Update in Firestore
    db = firestore.client()
    event_ref = db.collection("calendar_events").document(event_id)
    event_ref.update(update_data)
    
    # Get updated event
    updated_event = event_ref.get().to_dict()
    updated_event["id"] = event_id
    
    return CalendarEventInDB(**updated_event)