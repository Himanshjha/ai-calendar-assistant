
# langgraph_agent.py

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableLambda
from typing import TypedDict, Optional
import dateparser
from datetime import datetime, timedelta
from pytz import timezone
from dateparser.search import search_dates
from calendar_utils.calendar_api import check_availability, book_event
import streamlit as st
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

def detect_intent(state: AgentState) -> AgentState:
    prompt = f"What is the user's intent in this message? '{state['user_input']}' (Reply with one word: book, check, or unknown)"
    result = llm.invoke([HumanMessage(content=prompt)]).content.lower()

    if "book" in result:
        state["intent"] = "book"
    elif "check" in result or "free" in result or "available" in result:
        state["intent"] = "check"
    else:
        state["intent"] = "unknown"
    return state

def extract_time(state: AgentState) -> AgentState:
    local_tz = timezone("Asia/Kolkata")
    now = datetime.now(local_tz)

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
        # Grab the first matched datetime
        parsed = results[0][1]
        print("🕓 Matched time:", parsed)
        ist_time = parsed.astimezone(local_tz).replace(tzinfo=None)
        state["time_info"] = ist_time
    else:
        # Fallback: tomorrow same time
        print("⚠️ No time matched, using fallback.")
        state["time_info"] = now.replace(tzinfo=None) + timedelta(days=1)

    return state
def check_slot(state: AgentState) -> AgentState:
    start = state["time_info"]
    end = start + timedelta(minutes=30)

    events = check_availability(start, end)

    if events:
        state["confirmed"] = False
        state["reply"] = f"❌ You're busy at {start.strftime('%I:%M %p on %A')}. Cannot book — you're busy at that time."
    else:
        state["confirmed"] = True
        state["reply"] = f"✅ You're free at {start.strftime('%I:%M %p on %A')}!"
    return state

def book_slot(state: AgentState) -> AgentState:
    if state["confirmed"]:
        end = state["time_info"] + timedelta(minutes=30)
        link = book_event("Booked via AI", state["time_info"], end)
        state["reply"] += f" 📅 Event booked! 👉 {link}"
    # Remove the duplicate error message
    return state


builder = StateGraph(AgentState)
builder.add_node("DetectIntent", RunnableLambda(detect_intent))
builder.add_node("ExtractTime", RunnableLambda(extract_time))
builder.add_node("CheckSlot", RunnableLambda(check_slot))
builder.add_node("BookSlot", RunnableLambda(book_slot))

builder.set_entry_point("DetectIntent")
builder.add_edge("DetectIntent", "ExtractTime")
builder.add_edge("ExtractTime", "CheckSlot")
builder.add_edge("CheckSlot", "BookSlot")
builder.add_edge("BookSlot", END)

graph = builder.compile()

def run_agent(user_input: str):
    state = {
        "user_input": user_input,
        "intent": None,
        "time_info": None,
        "confirmed": None,
        "reply": None,
    }
    result = graph.invoke(state)
    return result["reply"]