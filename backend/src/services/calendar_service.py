"""Google Calendar service for schedule management.

Provides CRUD operations for Google Calendar events,
free/busy slot finding, and LINE display formatting.
"""

import logging
from datetime import datetime, timedelta, timezone

from googleapiclient.discovery import build
from sqlalchemy.orm import Session

from src.models.models import ConfirmationStatus, EventType, OAuthProvider
from src.services.color_defaults import get_color_for_event
from src.services.google_oauth import get_google_credentials
from src.utils.errors import ExternalServiceError, NotFoundError

logger = logging.getLogger(__name__)

CALENDAR_SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
]


def _build_calendar_client(user_id: str, db: Session):
    """Build an authenticated Google Calendar API client.

    Args:
        user_id: User UUID string.
        db: SQLAlchemy session.

    Returns:
        Google Calendar API service resource.
    """
    credentials = get_google_credentials(
        user_id=user_id,
        db=db,
        scopes=CALENDAR_SCOPES,
        provider=OAuthProvider.gcalendar,
    )
    return build("calendar", "v3", credentials=credentials)


def get_schedule(
    user_id: str,
    db: Session,
    date_from: str,
    date_to: str,
) -> list[dict]:
    """Get calendar events within a date range.

    Args:
        user_id: User UUID string.
        db: SQLAlchemy session.
        date_from: Start date in ISO format (YYYY-MM-DD).
        date_to: End date in ISO format (YYYY-MM-DD).

    Returns:
        List of event dicts with title, start, end, location, etc.
    """
    service = _build_calendar_client(user_id, db)

    time_min = f"{date_from}T00:00:00Z"
    time_max = f"{date_to}T23:59:59Z"

    try:
        result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy="startTime",
                maxResults=100,
            )
            .execute()
        )
    except Exception as e:
        logger.error("Google Calendar API error: %s", e)
        raise ExternalServiceError(service="Google Calendar", message=str(e))

    events = result.get("items", [])
    return [_format_event(ev) for ev in events]


def find_available_slots(
    user_id: str,
    db: Session,
    date: str,
    duration_minutes: int = 60,
) -> list[dict]:
    """Find available time slots on a given date using FreeBusy API.

    Args:
        user_id: User UUID string.
        db: SQLAlchemy session.
        date: Date in ISO format (YYYY-MM-DD).
        duration_minutes: Required slot duration in minutes.

    Returns:
        List of dicts with "start" and "end" times for available slots.
    """
    service = _build_calendar_client(user_id, db)

    time_min = f"{date}T08:00:00Z"
    time_max = f"{date}T20:00:00Z"

    try:
        freebusy = (
            service.freebusy()
            .query(
                body={
                    "timeMin": time_min,
                    "timeMax": time_max,
                    "items": [{"id": "primary"}],
                }
            )
            .execute()
        )
    except Exception as e:
        logger.error("Google Calendar FreeBusy API error: %s", e)
        raise ExternalServiceError(service="Google Calendar", message=str(e))

    busy_periods = freebusy.get("calendars", {}).get("primary", {}).get("busy", [])
    return _calculate_free_slots(
        busy_periods, time_min, time_max, duration_minutes
    )


def create_event(
    user_id: str,
    db: Session,
    event_data: dict,
) -> dict:
    """Create a new Google Calendar event.

    Args:
        user_id: User UUID string.
        db: SQLAlchemy session.
        event_data: Dict with summary, start, end, description, location,
                    event_type, confirmation_status.

    Returns:
        Created event dict formatted for display.
    """
    service = _build_calendar_client(user_id, db)

    event_type = EventType(event_data.get("event_type", "business"))
    confirmation = ConfirmationStatus(
        event_data.get("confirmation_status", "confirmed")
    )
    color_id = get_color_for_event(user_id, db, event_type, confirmation)

    body = {
        "summary": event_data["summary"],
        "start": _build_time_field(event_data["start"]),
        "end": _build_time_field(event_data["end"]),
        "colorId": color_id,
    }
    if event_data.get("description"):
        body["description"] = event_data["description"]
    if event_data.get("location"):
        body["location"] = event_data["location"]
    if confirmation == ConfirmationStatus.tentative:
        body["status"] = "tentative"

    try:
        created = (
            service.events()
            .insert(calendarId="primary", body=body)
            .execute()
        )
    except Exception as e:
        logger.error("Google Calendar create event error: %s", e)
        raise ExternalServiceError(service="Google Calendar", message=str(e))

    logger.info("Created calendar event %s for user %s", created.get("id"), user_id)
    return _format_event(created)


def update_event(
    user_id: str,
    db: Session,
    event_id: str,
    updates: dict,
) -> dict:
    """Update an existing Google Calendar event.

    Args:
        user_id: User UUID string.
        db: SQLAlchemy session.
        event_id: Google Calendar event ID.
        updates: Dict of fields to update (summary, start, end, etc.).

    Returns:
        Updated event dict formatted for display.
    """
    service = _build_calendar_client(user_id, db)

    # Fetch existing event
    try:
        existing = (
            service.events()
            .get(calendarId="primary", eventId=event_id)
            .execute()
        )
    except Exception as e:
        logger.error("Google Calendar get event error: %s", e)
        raise NotFoundError(resource="Calendar Event", resource_id=event_id)

    # Apply updates
    if "summary" in updates:
        existing["summary"] = updates["summary"]
    if "description" in updates:
        existing["description"] = updates["description"]
    if "location" in updates:
        existing["location"] = updates["location"]
    if "start" in updates:
        existing["start"] = _build_time_field(updates["start"])
    if "end" in updates:
        existing["end"] = _build_time_field(updates["end"])
    if "event_type" in updates or "confirmation_status" in updates:
        event_type = EventType(updates.get("event_type", "business"))
        confirmation = ConfirmationStatus(
            updates.get("confirmation_status", "confirmed")
        )
        existing["colorId"] = get_color_for_event(
            user_id, db, event_type, confirmation
        )

    try:
        updated = (
            service.events()
            .update(calendarId="primary", eventId=event_id, body=existing)
            .execute()
        )
    except Exception as e:
        logger.error("Google Calendar update event error: %s", e)
        raise ExternalServiceError(service="Google Calendar", message=str(e))

    logger.info("Updated calendar event %s for user %s", event_id, user_id)
    return _format_event(updated)


def delete_event(user_id: str, db: Session, event_id: str) -> bool:
    """Delete a Google Calendar event.

    Args:
        user_id: User UUID string.
        db: SQLAlchemy session.
        event_id: Google Calendar event ID.

    Returns:
        True if deleted successfully.
    """
    service = _build_calendar_client(user_id, db)

    try:
        service.events().delete(
            calendarId="primary", eventId=event_id
        ).execute()
    except Exception as e:
        logger.error("Google Calendar delete event error: %s", e)
        raise ExternalServiceError(service="Google Calendar", message=str(e))

    logger.info("Deleted calendar event %s for user %s", event_id, user_id)
    return True


def format_events_for_line(events: list[dict]) -> list[dict]:
    """Format events for LINE Flex Message display.

    Args:
        events: List of formatted event dicts.

    Returns:
        List of dicts ready for line_templates.schedule_summary_template().
    """
    return [
        {
            "title": ev.get("summary", "Untitled"),
            "start": ev.get("start_display", ""),
            "end": ev.get("end_display", ""),
            "location": ev.get("location"),
        }
        for ev in events
    ]


# ─── Private helpers ───────────────────────────────────────────


def _format_event(event: dict) -> dict:
    """Format a raw Google Calendar event into a standardized dict."""
    start = event.get("start", {})
    end = event.get("end", {})
    start_str = start.get("dateTime", start.get("date", ""))
    end_str = end.get("dateTime", end.get("date", ""))

    return {
        "id": event.get("id", ""),
        "summary": event.get("summary", "Untitled"),
        "description": event.get("description", ""),
        "location": event.get("location", ""),
        "start": start_str,
        "end": end_str,
        "start_display": _format_time_display(start_str),
        "end_display": _format_time_display(end_str),
        "status": event.get("status", "confirmed"),
        "color_id": event.get("colorId", ""),
        "html_link": event.get("htmlLink", ""),
    }


def _format_time_display(iso_str: str) -> str:
    """Convert ISO datetime to display format (HH:MM)."""
    if not iso_str or len(iso_str) <= 10:
        return iso_str  # Date-only events
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%H:%M")
    except ValueError:
        return iso_str


def _build_time_field(value: str) -> dict:
    """Build Google Calendar time field from ISO string.

    Returns dateTime field for datetime strings, date field for date-only.
    """
    if len(value) <= 10:
        return {"date": value}
    return {"dateTime": value, "timeZone": "Asia/Tokyo"}


def _calculate_free_slots(
    busy_periods: list[dict],
    time_min: str,
    time_max: str,
    duration_minutes: int,
) -> list[dict]:
    """Calculate free time slots from busy periods.

    Args:
        busy_periods: List of {"start": str, "end": str} busy periods.
        time_min: Start of search window (ISO format).
        time_max: End of search window (ISO format).
        duration_minutes: Minimum slot duration in minutes.

    Returns:
        List of {"start": str, "end": str} available slots.
    """
    def parse_dt(s: str) -> datetime:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))

    window_start = parse_dt(time_min)
    window_end = parse_dt(time_max)
    min_duration = timedelta(minutes=duration_minutes)

    # Sort busy periods by start time
    sorted_busy = sorted(busy_periods, key=lambda x: x["start"])

    free_slots = []
    current = window_start

    for busy in sorted_busy:
        busy_start = parse_dt(busy["start"])
        busy_end = parse_dt(busy["end"])

        if current < busy_start:
            gap = busy_start - current
            if gap >= min_duration:
                free_slots.append({
                    "start": current.isoformat(),
                    "end": busy_start.isoformat(),
                })
        current = max(current, busy_end)

    # Check remaining time after last busy period
    if current < window_end:
        gap = window_end - current
        if gap >= min_duration:
            free_slots.append({
                "start": current.isoformat(),
                "end": window_end.isoformat(),
            })

    return free_slots
