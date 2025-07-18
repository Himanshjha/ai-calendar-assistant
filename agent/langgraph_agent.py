
# langgraph_agent.py

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableLambda
from typing import TypedDict, Optional
from datetime import datetime, timedelta
from pytz import timezone
from dateparser.search import search_dates
from calendar_utils.calendar_api import check_availability, book_event

google_api_key = os.getenv("GOOGLE_API_KEY")

llm = ChatGoogleGenerativeAI(
    model="models/gemini-1.5-flash",
    google_api_key=google_api_key
)

class AgentState(TypedDict):
    user_input: str
    intent: Optional[str]
    time_info: Optional[datetime]
    confirmed: Optional[bool]
    reply: Optional[str]

# ---------------------------
# Step 1: Detect Intent
# ---------------------------
def detect_intent(state: AgentState) -> str:
    user_msg = state["user_input"].strip().lower()
    greetings = ['hi', 'hello', 'hey', 'hii', 'good morning', 'good evening']

    if user_msg in greetings or len(user_msg.split()) <= 3 and not any(word in user_msg for word in ["book", "free", "available", "schedule", "meeting", "call"]):
        state["intent"] = "unknown"
        return "unknown"

    prompt = (
        f"The user said: '{state['user_input']}'. "
        "Decide the user's intent. Respond with exactly one of: 'book', 'check', or 'unknown'. "
        "Only reply 'book' if they clearly want to schedule or create an event. "
        "Reply 'check' if they're asking about free time, availability, or schedule. "
        "Reply 'unknown' if it's a greeting, vague message, or unclear."
    )

    try:
        result = llm.invoke([HumanMessage(content=prompt)]).content.lower()
        if "book" in result:
            state["intent"] = "book"
        elif "check" in result or "free" in result or "available" in result:
            state["intent"] = "check"
        else:
            state["intent"] = "unknown"
        print("🔍 Detected Intent:", state["intent"])
        return state["intent"]
    except Exception:
        state["intent"] = "quota_error"
        state["reply"] = "😵 Gemini quota exceeded. Please try again later."
        return "quota_error"

# ---------------------------
# Step 2: Extract Time
# ---------------------------
def extract_time(state: AgentState) -> AgentState:
    local_tz = timezone("Asia/Kolkata")
    now = datetime.now(local_tz)
    try:
        results = search_dates(
            state["user_input"],
            settings={
                'PREFER_DATES_FROM': 'future',
                'RELATIVE_BASE': now,
                'TIMEZONE': 'Asia/Kolkata',
                'RETURN_AS_TIMEZONE_AWARE': True
            }
        )
        if results:
            parsed = results[0][1]
            ist_time = parsed.astimezone(local_tz).replace(tzinfo=None)

            text = results[0][0].lower()
            if "afternoon" in text and ist_time.hour < 12:
                ist_time = ist_time.replace(hour=15, minute=0)
            elif "evening" in text and ist_time.hour < 17:
                ist_time = ist_time.replace(hour=18, minute=0)
            elif "morning" in text and ist_time.hour < 8:
                ist_time = ist_time.replace(hour=10, minute=0)

            state["time_info"] = ist_time
        else:
            fallback_time = (now + timedelta(days=1)).replace(hour=15, minute=0, second=0, microsecond=0)
            state["time_info"] = fallback_time

    except Exception:
        state["reply"] = "😕 Sorry, I couldn't understand the time in your message."
        state["intent"] = "unknown"
        return state

    return state

# ---------------------------
# Step 3: Check Availability
# ---------------------------
def check_slot(state: AgentState) -> AgentState:
    if not state["time_info"]:
        print("⚠️ Missing time_info. Skipping check.")
        state["reply"] = "❗ I couldn't understand the time. Please rephrase your query."
        state["intent"] = "unknown"
        return state

    start = state["time_info"]
    end = start + timedelta(minutes=30)

    events = check_availability(start, end)

    if events:
        state["confirmed"] = False
        state["reply"] = f"❌ You're busy at {start.strftime('%I:%M %p on %A')}."
    else:
        state["confirmed"] = True
        state["reply"] = f"✅ You're free at {start.strftime('%I:%M %p on %A')}!"

    return state


# ---------------------------
# Step 4: Book Event
# ---------------------------
def book_slot(state: AgentState) -> AgentState:
    if state.get("confirmed"):
        try:
            end = state["time_info"] + timedelta(minutes=30)
            link = book_event("Booked via AI", state["time_info"], end)
            state["reply"] += f" 📅 Event booked! 👉 {link}"
        except Exception as e:
            state["reply"] += f" 🚫 Booking failed: {e}"
    return state

# ---------------------------
# Step 5: Handle Unknown
# ---------------------------
def handle_unknown(state: AgentState) -> AgentState:
    if not state.get("reply"):
        state["reply"] = "❓ Sorry, I didn't understand. Try asking to *book* or *check* availability."
    return state

# ---------------------------
# LangGraph Workflow
# ---------------------------
builder = StateGraph(AgentState)

builder.add_node("DetectIntent", RunnableLambda(detect_intent))
builder.add_node("ExtractTime", RunnableLambda(extract_time))
builder.add_node("CheckSlot", RunnableLambda(check_slot))
builder.add_node("BookSlot", RunnableLambda(book_slot))
builder.add_node("HandleUnknown", RunnableLambda(handle_unknown))
builder.add_node("QuotaError", RunnableLambda(lambda s: s))

builder.set_entry_point("DetectIntent")

builder.add_conditional_edges("DetectIntent", {
    "book": RunnableLambda(extract_time),
    "check": RunnableLambda(extract_time),
    "unknown": RunnableLambda(handle_unknown),
    "quota_error": RunnableLambda(lambda s: s),
})

builder.add_edge("ExtractTime", "CheckSlot")

builder.add_conditional_edges("CheckSlot", {
    "book": RunnableLambda(book_slot),
    "check": RunnableLambda(lambda s: s),  # previously "check": END ❌
    "unknown": RunnableLambda(handle_unknown),
})


builder.add_edge("BookSlot", END)
builder.add_edge("HandleUnknown", END)
builder.add_edge("QuotaError", END)

graph = builder.compile()

# ---------------------------
# Final Agent Runner
# ---------------------------
def run_agent(user_input: str):
    state = {
        "user_input": user_input,
        "intent": None,
        "time_info": None,
        "confirmed": None,
        "reply": None,
    }
    result = graph.invoke(state)

    if not result.get("reply"):
        print("⚠️ No reply returned from graph:", result)
        result["reply"] = "⚠️ No response generated. Please try again."

    return result["reply"]
