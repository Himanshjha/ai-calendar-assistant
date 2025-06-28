from datetime import datetime, timedelta
from calendar_api import get_calendar_service, check_availability, book_event

print("🔁 Authenticating...")
service = get_calendar_service()

print("✅ Checking availability for the next hour...")
now = datetime.utcnow()
one_hour_later = now + timedelta(hours=1)

events = check_availability(now, one_hour_later)
if events:
    print("❌ Calendar is busy. Found events:")
for event in events:
    print("🔸", event.get('summary', '[No Title]'))
    print("   ⏰ Start:", event.get('start', {}).get('dateTime', '[No Start]'))
    print("   🛑 End  :", event.get('end', {}).get('dateTime', '[No End]'))
 
else:
    print("✅ Calendar is free! Booking test event...")
    link = book_event("Test Booking with Himanshu", now + timedelta(minutes=5), now + timedelta(minutes=35))
    print("📅 Event booked successfully:", link)
