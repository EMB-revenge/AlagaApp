from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict
from datetime import datetime, timedelta, date, time
import calendar as cal
import firebase_admin
from firebase_admin import firestore

# Import models
from ..models.calendar_event_model import (
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
from .users import get_authenticated_user, authorize_care_profile_access
from ..models.user_model import UserInDB

# Import FieldValue for server timestamps
from google.cloud.firestore import FieldValue

from ..main import db

router = APIRouter(
    prefix="/calendar",
    tags=["calendar"],
    responses={404: {"description": "Not found"}},
)

# Helper functions
async def get_calendar_event_by_id(event_id: str, current_user: UserInDB) -> Optional[CalendarEventInDB]:
    """Get a calendar event by ID and check authorization"""
    try:
        event_ref = db.collection("calendar_events").document(event_id)
        event_doc = event_ref.get()
        
        if not event_doc.exists:
            return None # Event not found
        
        event_data = event_doc.to_dict()
        event_data["id"] = event_doc.id
        
        # Check if event belongs to the current user's care profile (basic authz)
        # More sophisticated authz might check user_id directly or shared access
        if 'care_profile_id' in event_data:
             await authorize_care_profile_access(event_data['care_profile_id'], current_user)
        else:
             # If no care_profile_id, perhaps check if user_id matches? Define your rule.
             # Assuming events without care_profile_id might be personal user events
             if 'user_id' in event_data and event_data['user_id'] != current_user.id:
                 raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this event (no care profile)")
             # If no user_id either, maybe it's an error or global event? Decide policy.

        # Pydantic model will handle conversion from Firestore timestamps/dates/times
        return CalendarEventInDB(**event_data)

    except firestore.exceptions.FirebaseError as e:
        print(f"Firestore error in get_calendar_event_by_id: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error retrieving event: {str(e)}")
    except HTTPException:
        raise # Re-raise HTTPException from authorization
    except Exception as e:
        print(f"Unexpected error in get_calendar_event_by_id: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")

async def get_events_by_date_range(current_user: UserInDB, care_profile_id: str, start_date: date, end_date: date) -> List[CalendarEventInDB]:
    """Get all events for a user and care profile within a date range"""
    try:
        # Authorize access to the care profile
        await authorize_care_profile_access(care_profile_id, current_user)

        # Use datetime objects for Firestore range queries on timestamp fields
        # Assuming calendar events are stored with a datetime timestamp or similar.
        # If only date is stored, query needs adjustment.
        # Assuming 'date' field in Firestore is stored as a Timestamp or datetime-like.
        
        # For querying based on the 'date' field which is now a date type in the model:
        # If stored as Firestore Date/Timestamp, compare directly.
        # If stored as ISO string, compare strings (YYYY-MM-DD format works lexicographically).
        # Let's assume it's stored in a way that direct date/timestamp comparison works or ISO string comparison works correctly for YYYY-MM-DD.
        
        # To query a 'date' field (stored as YYYY-MM-DD string or Firestore Date):
        # start_date_str = start_date.isoformat()
        # end_date_str = end_date.isoformat()

        # To query a 'timestamp' field (datetime stored as Firestore Timestamp):
        # start_datetime = datetime.combine(start_date, datetime.min.time())
        # end_datetime = datetime.combine(end_date, datetime.max.time())

        # Based on CalendarEventBase model having 'date: date' and 'time: time':
        # It's likely events are queried by 'date'. Querying by a date range on a 'date' field stored as Firestore Date is direct.
        # If stored as ISO string, YYYY-MM-DD string comparison works.
        
        # Assuming 'date' is stored as a Firestore Date or YYYY-MM-DD string:
        events_ref = db.collection("calendar_events")\
            .where("care_profile_id", "==", care_profile_id)\
            .where("date", ">=", start_date)\
            .where("date", "<=", end_date)\
            .get()
        
        # If you need to query by a datetime field (e.g., for reminders):
        # events_ref = db.collection("calendar_events")\
        #     .where("care_profile_id", "==", care_profile_id)\
        #     .where("scheduled_time", ">=", start_datetime)\
        #     .where("scheduled_time", "<=", end_datetime)\
        #     .get()

        events = []
        for event_doc in events_ref:
            event_data = event_doc.to_dict()
            event_data["id"] = event_doc.id
            # Pydantic model handles conversion from Firestore data
            events.append(CalendarEventInDB(**event_data))
        
        return events

    except firestore.exceptions.FirebaseError as e:
        print(f"Firestore error in get_events_by_date_range: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error retrieving events: {str(e)}")
    except HTTPException:
        raise # Re-raise HTTPException from authorization
    except Exception as e:
        print(f"Unexpected error in get_events_by_date_range: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")

async def get_events_by_date(current_user: UserInDB, care_profile_id: str, date: date) -> List[CalendarEventInDB]:
    """Get all events for a user and care profile on a specific date"""
    return await get_events_by_date_range(current_user, care_profile_id, date, date)

# check_calendar_access helper can remain as is or be removed if subscription logic moves
# def check_calendar_access(user_subscription):
#     """Check if user has access to enhanced calendar features"""
#     has_enhanced_calendar = False
    
#     if user_subscription and user_subscription.tier == SubscriptionTier.PREMIUM:
#         has_enhanced_calendar = True
    
#     return has_enhanced_calendar

# Routes
@router.post("/events", response_model=CalendarEventInDB, status_code=status.HTTP_201_CREATED)
async def create_calendar_event(event: CalendarEventCreate, current_user: UserInDB = Depends(get_authenticated_user)):
    """Create a new calendar event"""
    try:
        # Authorize access to the care profile specified in the request
        if event.care_profile_id:
             await authorize_care_profile_access(event.care_profile_id, current_user)
        else:
             # Decide policy for events without care_profile_id (personal events?)
             # If personal, maybe verify event.user_id is current_user.id or assume it.
             # Assuming for now events must have a care_profile_id for authorization.
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Care profile ID is required for calendar events.")

        # Convert Pydantic model to dict for Firestore
        event_data_to_store = event.model_dump(exclude_unset=True)
        
        # Pydantic models with date/time/datetime types and json_encoders should
        # handle conversion to Firestore-compatible formats (ISO strings or native types).
        # If storing as Firestore native Timestamp/Date/Time, no manual conversion needed here.

        firestore_data = {
            **event_data_to_store, # Includes title, type, date, time, care_profile_id, details, etc.
            "user_id": current_user.id, # Ensure user_id is set from authenticated user
            "created_at": FieldValue.serverTimestamp(),
            "updated_at": FieldValue.serverTimestamp()
        }

        # Add a new document with a generated ID
        event_ref = db.collection("calendar_events").document()
        event_ref.set(firestore_data)
        
        # Retrieve the created document to return as CalendarEventInDB
        created_event_doc = event_ref.get()
        if not created_event_doc.exists:
             # This is an unexpected error if set() was successful
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve event after creation.")

        return CalendarEventInDB(id=created_event_doc.id, **created_event_doc.to_dict())

    except HTTPException as http_exc:
        raise http_exc # Re-raise HTTPException from authorization
    except firestore.exceptions.FirebaseError as e:
        print(f"Firestore error during event creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during event creation: {str(e)}"
        )
    except Exception as e:
        print(f"Unexpected error during event creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during event creation: {str(e)}"
        )

@router.get("/events/{event_id}", response_model=CalendarEventInDB)
async def get_calendar_event(event_id: str, current_user: UserInDB = Depends(get_authenticated_user)):
    """Get a calendar event by ID"""
    event = await get_calendar_event_by_id(event_id, current_user)
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Authorization check is now handled within get_calendar_event_by_id helper.
    
    return event

@router.put("/events/{event_id}", response_model=CalendarEventInDB)
async def update_calendar_event(event_id: str, event_update: CalendarEventUpdate, current_user: UserInDB = Depends(get_authenticated_user)):
    """Update a calendar event"""
    try:
        event_ref = db.collection("calendar_events").document(event_id)
        
        # Use the helper to get the existing event and perform authorization check
        existing_event = await get_calendar_event_by_id(event_id, current_user)
        
        if not existing_event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
        
        # Authorization check is handled by get_calendar_event_by_id.
        
        # Prepare update data
        update_data = event_update.model_dump(exclude_unset=True)
        
        if not update_data:
             # Optional: return current event data or a message if no fields provided for update
             return existing_event # Return current event data if no updates were provided

        # Use server timestamp for updated_at
        update_data["updated_at"] = FieldValue.serverTimestamp()
    
        # Update in Firestore
        event_ref.update(update_data)
        
        # Get updated event from Firestore to return in response
        updated_event_doc = event_ref.get()
        if not updated_event_doc.exists:
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve event after update.")

        return CalendarEventInDB(id=updated_event_doc.id, **updated_event_doc.to_dict())

    except HTTPException as http_exc:
        raise http_exc # Re-raise HTTPException from authorization or not found
    except firestore.exceptions.FirebaseError as e:
        print(f"Firestore error during event update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during event update: {str(e)}"
        )
    except Exception as e:
        print(f"Unexpected error during event update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during event update"
        )

@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_calendar_event(event_id: str, current_user: UserInDB = Depends(get_authenticated_user)):
    """Delete a calendar event"""
    try:
        event_ref = db.collection("calendar_events").document(event_id)
        
        # Use the helper to get the existing event and perform authorization check
        existing_event = await get_calendar_event_by_id(event_id, current_user)
        
        if not existing_event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
        
        # Authorization check is handled by get_calendar_event_by_id.

        # Delete from Firestore
        event_ref.delete()
        
        # Note: HTTP 204 response typically has no body.
        return # Return None for 204 No Content

    except HTTPException as http_exc:
        raise http_exc # Re-raise HTTPException from authorization or not found
    except firestore.exceptions.FirebaseError as e:
        print(f"Firestore error during event deletion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during event deletion: {str(e)}"
        )
    except Exception as e:
        print(f"Unexpected error during event deletion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during event deletion"
        )

@router.get("/events/day/{date}", response_model=CalendarDay)
async def get_day_events(
    care_profile_id: str,
    date: date = Depends(), # Use Depends to parse date from path parameter
    current_user: UserInDB = Depends(get_authenticated_user),
):
    """Get all events for a specific day"""
    # Authorization check is handled within get_events_by_date_range helper
    events = await get_events_by_date(current_user, care_profile_id, date)
    
    return CalendarDay(
        date=date, # date is now a date object
        events=events
    )

@router.get("/events/month/{year}/{month}", response_model=CalendarMonth)
async def get_month_events(
    year: int,
    month: int,
    care_profile_id: str,
    current_user: UserInDB = Depends(get_authenticated_user)
):
    """Get all events for a specific month"""
    try:
        # Authorization check is handled within get_events_by_date_range helper
        
        first_day_of_month = date(year, month, 1)
        _, num_days_in_month = cal.monthrange(year, month)
        last_day_of_month = date(year, month, num_days_in_month)

        # Use date objects for the helper function
        all_month_events = await get_events_by_date_range(current_user, care_profile_id, first_day_of_month, last_day_of_month)

        # Create CalendarMonth response
        days_in_month_response = {}
        for day_num in range(1, num_days_in_month + 1):
            current_day_obj = date(year, month, day_num)
            # Filter events for the current day from all_month_events
            # Assuming event.date is a date object after Pydantic parsing from Firestore
            day_events = [event for event in all_month_events if event.date == current_day_obj]
            
            days_in_month_response[current_day_obj.isoformat()] = CalendarDay(
                date=current_day_obj, # date is a date object
                events=day_events
            )
            
        # Sort days by date for consistent response order (optional)
        sorted_days_response = dict(sorted(days_in_month_response.items()))

        return CalendarMonth(
            year=year,
            month=month,
            days=sorted_days_response
        )

    except HTTPException as http_exc:
        raise http_exc # Re-raise HTTPException from authorization
    except Exception as e:
        print(f"Unexpected error retrieving month events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.get("/events/today", response_model=CalendarDay)
async def get_today_events(
    care_profile_id: str,
    current_user: UserInDB = Depends(get_authenticated_user)
):
    """Get all events for the current day"""
    # Authorization check is handled within get_events_by_date helper
    today_date = date.today()
    events = await get_events_by_date(current_user, care_profile_id, today_date)

    return CalendarDay(
        date=today_date, # date is a date object
        events=events
    )

@router.post("/events/mark-status/{event_id}", response_model=CalendarEventInDB)
async def mark_event_status(
    event_id: str,
    status: EventStatus,
    current_user: UserInDB = Depends(get_authenticated_user)
):
    """Mark the status of a calendar event"""
    try:
        event_ref = db.collection("calendar_events").document(event_id)
        
        # Use the helper to get the existing event and perform authorization check
        existing_event = await get_calendar_event_by_id(event_id, current_user)
        
        if not existing_event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
        
        # Authorization check is handled by get_calendar_event_by_id.

        # Prepare update data
        update_data = {
            "status": status.value, # Use the string value of the Enum
            "updated_at": FieldValue.serverTimestamp()
        }

        # Update in Firestore
        event_ref.update(update_data)
        
        # Get updated event from Firestore to return in response
        updated_event_doc = event_ref.get()
        if not updated_event_doc.exists:
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve event after status update.")

        # Return the updated event (Pydantic model will handle conversion)
        return CalendarEventInDB(id=updated_event_doc.id, **updated_event_doc.to_dict())

    except HTTPException as http_exc:
        raise http_exc # Re-raise HTTPException from authorization or not found
    except firestore.exceptions.FirebaseError as e:
        print(f"Firestore error during event status update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during event status update: {str(e)}"
        )
    except Exception as e:
        print(f"Unexpected error during event status update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during event status update"
        )