import streamlit as st
import requests

# Page config
st.set_page_config(page_title="AI Calendar Assistant", layout="centered")

# Session state to store theme mode
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

# Toggle theme
mode_toggle = st.toggle("🌗 Toggle Dark Mode", value=st.session_state.dark_mode)
st.session_state.dark_mode = mode_toggle

# Theme Colors
bg_color = "#1e1e2f" if mode_toggle else "#f3f4f6"
text_color = "#f9fafb" if mode_toggle else "#1f2937"
card_bg = "#2a2a40" if mode_toggle else "#ffffff"
button_color = "#6366f1" if mode_toggle else "#2563eb"



# Inject CSS
st.markdown(
    f"""
    <style>
        body {{
            background-color: {bg_color};
            color: {text_color};
        }}
        .stApp {{
            background: linear-gradient(135deg, #4f46e5 0%, #8b5cf6 100%);
            background-attachment: fixed;
        }}
        .main-box {{
            background-color: {card_bg};
            color: {text_color};
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0px 8px 20px rgba(0,0,0,0.2);
            margin-top: 2rem;
        }}
        .chat-output {{
            font-size: 1.1rem;
            background-color: #3b3b55;
            color: #ffffff;
            padding: 1rem;
            margin-top: 1rem;
            border-radius: 12px;
        }}
        .submit-btn {{
            background-color: {button_color};
            color: white;
            border: none;
            padding: 0.6rem 1.2rem;
            font-size: 1rem;
            border-radius: 8px;
            font-weight: 600;
            margin-top: 1rem;
        }}
        .submit-btn:hover {{
            background-color: #4338ca;
        }}
    </style>
    """,
    unsafe_allow_html=True
)

# Header
st.markdown(f"<h1 style='text-align: center; color:{text_color}'>📅 AI Calendar Assistant</h1>", unsafe_allow_html=True)

# Main Chat Container
st.markdown("<div class='main-box'>", unsafe_allow_html=True)

st.markdown("### 🤖 Ask me something like:")
st.markdown("- Book a meeting for Monday at 4 PM")
st.markdown("- Am I free tomorrow at 3 PM?")

query = st.text_input("💬 Your Message:")

if st.button("🚀 Ask", key="ask", help="Submit your message"):
    with st.spinner("🤖 Thinking..."):
        try:
            res = requests.post("http://127.0.0.1:8000/ask", json={"query": query})
            if res.status_code == 200:
                st.markdown(f"<div class='chat-output'>{res.json()['response']}</div>", unsafe_allow_html=True)
            else:
                st.error("❌ API Error: " + str(res.status_code))
        except Exception as e:
            st.error(f"🚨 Connection error: {e}")

st.markdown("</div>", unsafe_allow_html=True)
