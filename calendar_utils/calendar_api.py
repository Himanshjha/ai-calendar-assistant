import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime
import streamlit as st

# Scopes for accessing calendar events
SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service():
    # Load service account from Streamlit secrets
    service_account_info = json.loads(st.secrets["GCP_SERVICE_ACCOUNT"])
    credentials = service_account.Credentials.from_service_account_info(
        service_account_info, scopes=SCOPES
    )
    service = build('calendar', 'v3', credentials=credentials)
    return service

def check_availability(start_time, end_time):
    service = get_calendar_service()
    time_min = start_time.isoformat() + 'Z'
    time_max = end_time.isoformat() + 'Z'

    print(f"Start UTC: {time_min}")
    print(f"End UTC: {time_max}")

    events_result = service.events().list(
        calendarId='primary',
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    return events_result.get('items', [])

def book_event(summary, start_time, end_time):
    service = get_calendar_service()

    event = {
        'summary': summary,
        'start': {'dateTime': start_time.isoformat(), 'timeZone': 'Asia/Kolkata'},
        'end': {'dateTime': end_time.isoformat(), 'timeZone': 'Asia/Kolkata'},
    }

    created_event = service.events().insert(calendarId='primary', body=event).execute()
    return created_event.get('htmlLink')
