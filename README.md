# 📅 AI Calendar Assistant

An intelligent conversational agent to **check availability** and **book meetings** using your **Google Calendar** — built for the TailorTalk backend assignment.

## 🔧 Tech Stack

- **Backend**: FastAPI
- **Agent Framework**: LangGraph + Gemini (Google GenAI)
- **Frontend**: Streamlit
- **Calendar**: Google Calendar API

---

## 🚀 How to Run

### 1. 🔐 Setup Google Calendar API

- Place your `credentials.json` inside `calendar_utils/`
- Run:
  ```bash
  python calendar_utils/test_calendar.py
This will authenticate and generate token.pickle.

2. ⚙️ Install Dependencies
bash
Copy
Edit
pip install -r requirements.txt
3. ▶️ Start FastAPI Backend
bash
Copy
Edit
uvicorn api.main:app --reload
Server runs at: http://127.0.0.1:8000
API endpoint: POST /ask with JSON { "query": "Book a meeting..." }

4. 🖥️ Run Streamlit Frontend
bash
Copy
Edit
cd frontend
streamlit run streamlit_app.py
Ask in natural language like:
“Book a meeting for Monday at 4 PM”
“Am I free tomorrow at 5 PM?”

✅ Features
Natural language understanding using Gemini

Smart time extraction via dateparser

Checks Google Calendar availability

Books meeting with confirmation & shareable link

Works in Indian Standard Time (Asia/Kolkata)

