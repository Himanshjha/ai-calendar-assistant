import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime
import os
import pytz
# Scopes for accessing calendar events
SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service():
    # Load service account from Streamlit secrets

    service_account_info = json.loads(os.environ["GCP_SERVICE_ACCOUNT"])
    credentials = service_account.Credentials.from_service_account_info(
        service_account_info, scopes=SCOPES
    )
    service = build('calendar', 'v3', credentials=credentials)
    return service

def check_availability(start_dt, end_dt):
    service = get_calendar_service()

    # Ensure timezone-aware datetimes
    ist = pytz.timezone("Asia/Kolkata")
    if start_dt.tzinfo is None:
        start_dt = ist.localize(start_dt)
    if end_dt.tzinfo is None:
        end_dt = ist.localize(end_dt)

    # Convert to UTC and format as ISO string with Z
    start_utc = start_dt.astimezone(pytz.utc).replace(tzinfo=None).isoformat() + 'Z'
    end_utc = end_dt.astimezone(pytz.utc).replace(tzinfo=None).isoformat() + 'Z'


    print("📤 Sending to Google Calendar API:")
    print("Start UTC:", start_utc)
    print("End UTC:", end_utc)

    # Fetch events between start and end
    events_result = service.events().list(
        calendarId='primary',
        timeMin=start_utc,
        timeMax=end_utc,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])

    print(f"📋 {len(events)} events fetched")
    for event in events:
        print("🔸", event.get("summary", "[No Title]"))
        print("   Start:", event.get("start"))
        print("   End  :", event.get("end"))

    # Check overlap manually
    for event in events:
        start_str = event.get('start', {}).get('dateTime')
        end_str = event.get('end', {}).get('dateTime')
        if start_str and end_str:
            try:
                existing_start = parse(start_str)
                existing_end = parse(end_str)

                # Overlap condition: Start < End and End > Start
                if existing_start < end_dt and existing_end > start_dt:
                    print("⚠️ Overlapping event found:", event.get("summary", "[No Title]"))
                    return [event]
            except Exception as e:
                print("⚠️ Error parsing event time:", e)

    return []  # No conflicts found



def book_event(summary, start_time, end_time):
    service = get_calendar_service()

    ist = pytz.timezone("Asia/Kolkata")

    # Ensure timezone-aware datetimes
    if start_time.tzinfo is None:
        start_time = ist.localize(start_time)
    if end_time.tzinfo is None:
        end_time = ist.localize(end_time)

    event = {
        'summary': summary,
        'start': {
            'dateTime': start_time.isoformat(),
            'timeZone': 'Asia/Kolkata',
        },
        'end': {
            'dateTime': end_time.isoformat(),
            'timeZone': 'Asia/Kolkata',
        },
        'reminders': {
            'useDefault': True,
        },
    }

    created_event = service.events().insert(calendarId='primary', body=event).execute()
    print("📅 Event successfully booked:", created_event.get("htmlLink"))
    return created_event.get('htmlLink')
