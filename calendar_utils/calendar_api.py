from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import datetime
import os
import pickle
import pytz
from dateutil.parser import parse
from google.auth.transport.requests import Request

# Google Calendar API scope
SCOPES = ['https://www.googleapis.com/auth/calendar']
TOKEN_PATH = 'calendar_utils/token.pickle'
CREDENTIALS_PATH = 'calendar_utils/credentials.json'

def get_calendar_service():
    creds = None

    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)
    return service

def check_availability(start_dt, end_dt):
    service = get_calendar_service()

    # Ensure timezone-aware datetimes
    ist = pytz.timezone("Asia/Kolkata")
    if start_dt.tzinfo is None:
        start_dt = ist.localize(start_dt)
    if end_dt.tzinfo is None:
        end_dt = ist.localize(end_dt)

    # Convert to UTC
    start_utc = start_dt.astimezone(pytz.utc).isoformat(timespec='seconds')
    end_utc = end_dt.astimezone(pytz.utc).isoformat(timespec='seconds')

    print("📤 Sending to Google Calendar API:")
    print("Start UTC:", start_utc)
    print("End UTC:", end_utc)

    # Call the Calendar API
    events_result = service.events().list(
        calendarId='primary',
        timeMin=start_utc,
        timeMax=end_utc,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    all_events = events_result.get('items', [])

    # 📋 DEBUG: Log all raw events
    print("📋 Raw events fetched:")
    for event in all_events:
        print("🔸", event.get("summary", "[No Title]"))
        print("   Start:", event.get("start"))
        print("   End  :", event.get("end"))

    # Filter valid events (ignore all-day or dummy long blocks > 1 day)
    valid_events = []
    for event in all_events:
        start_str = event.get('start', {}).get('dateTime')
        end_str = event.get('end', {}).get('dateTime')
        if start_str and end_str:
            try:
                start = parse(start_str)
                end = parse(end_str)
                duration = end - start
                if duration.total_seconds() <= 86400:  # ≤ 1 day
                    valid_events.append(event)
            except Exception as e:
                print("⚠️ Error parsing event times:", e)

    return valid_events



def book_event(summary, start_dt, end_dt):
    service = get_calendar_service()
    ist = pytz.timezone("Asia/Kolkata")

    # Localize start and end if needed
    if start_dt.tzinfo is None:
        start_dt = ist.localize(start_dt)
    if end_dt.tzinfo is None:
        end_dt = ist.localize(end_dt)
        

    event = {
        'summary': summary,
        'start': {
            # Since microseconds are now removed earlier, isoformat() here will be fine
            'dateTime': start_dt.isoformat(), 
            'timeZone': 'Asia/Kolkata',
        },
        'end': {
            # Same here
            'dateTime': end_dt.isoformat(),   
            'timeZone': 'Asia/Kolkata',
        },
        'reminders': {
            'useDefault': True,
        },
    }

    event_result = service.events().insert(calendarId='primary', body=event).execute()
    return event_result.get('htmlLink')