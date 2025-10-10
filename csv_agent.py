from __future__ import annotations
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

import streamlit as st
import pdfplumber
import os
import json
import re
import datetime


def app():
    # Redirect if user not logged in
    if "logged_in" not in st.session_state or not st.session_state.logged_in:
        st.warning("You must log in first to access the chatbot.")
        st.stop()

    # ──────────────────────────────────────────────────────────────
    # 0) Streamlit Setup
    # ──────────────────────────────────────────────────────────────
    st.set_page_config(page_title="Elite CAD & Building Ops Chatbot", layout="wide")
    st.image("EliteLogo.jpg", width=180)
    st.title("Elite CAD & Building Operations AI Chatbot")
    os.makedirs("chat_logs", exist_ok=True)

    # ──────────────────────────────────────────────────────────────
    # 1) API Key Setup
    # ──────────────────────────────────────────────────────────────
    openai_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
    if not openai_key:
        st.error("Missing OPENAI_API_KEY.")
        st.stop()

    # ──────────────────────────────────────────────────────────────
    # 2) Model Initialization
    # ──────────────────────────────────────────────────────────────
    try:
        model = ChatOpenAI(api_key=openai_key, model="gpt-4o")
    except Exception as e:
        st.error("Failed to initialize ChatOpenAI:")
        st.exception(e)
        st.stop()

    # ──────────────────────────────────────────────────────────────
    # 3) Domain Keywords & Helpers
    # ──────────────────────────────────────────────────────────────
    ALLOWED_KEYWORDS = [
        "building", "construction", "cad", "design", "drafting", "maintenance", "hvac",
        "inspection", "roof", "electrical", "plumbing", "prototype", "mechanical",
        "facility", "repair", "renovation", "floor plan", "architectural", "engineering",
        "structural", "filter", "thermostat", "duct", "chiller", "boiler", "temperature",
        "energy", "airflow", "motor", "pump", "equipment", "safety", "code compliance",
        "circuit", "fuse", "wiring", "breaker", "water damage", "leak", "vibration"
    ]

    def is_domain_question(question: str) -> bool:
        return any(k in question.lower() for k in ALLOWED_KEYWORDS)

    def is_relevant_content(text) -> bool:
        return any(k in str(text).lower() for k in ALLOWED_KEYWORDS)

    def sanitize_filename(name):
        return re.sub(r'[^\w\s-]', '', name).strip().replace(" ", "_")[:50]

    def generate_title_from_message(msg):
        msg = msg.strip().capitalize()
        return msg[:60] + "..." if len(msg) > 60 else msg

    # ──────────────────────────────────────────────────────────────
    # 4) PDF Upload
    # ──────────────────────────────────────────────────────────────
    uploaded_pdfs = st.file_uploader("Upload HVAC / CAD PDFs (optional):", type="pdf", accept_multiple_files=True)
    pdf_text = ""
    if uploaded_pdfs:
        for up in uploaded_pdfs:
            st.success(f"Loaded PDF: {up.name}")
            try:
                with pdfplumber.open(up) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            pdf_text += text + "\n"
            except Exception as e:
                st.warning(f"Couldn’t parse {up.name}: {e}")

    # ──────────────────────────────────────────────────────────────
    # 5) Session State Setup
    # ──────────────────────────────────────────────────────────────
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "chat_title" not in st.session_state:
        st.session_state.chat_title = None
    if "current_session" not in st.session_state:
        st.session_state.current_session = None
    if "new_chat_started" not in st.session_state:
        st.session_state.new_chat_started = False

    # ──────────────────────────────────────────────────────────────
    # 6) Sidebar UI & Chat Selection
    # ──────────────────────────────────────────────────────────────
    st.sidebar.header("🗂️ Chat Sessions")
    log_files = sorted(os.listdir("chat_logs"), reverse=True)
    titles = ["➕ Start New Chat"] + [f.replace(".json", "") for f in log_files]
    selected = st.sidebar.radio("Select a chat to view or continue:", titles)

    if selected == "➕ Start New Chat":
        if not st.session_state.new_chat_started:
            st.session_state.chat_history = []
            st.session_state.chat_title = None
            st.session_state.current_session = None
            st.session_state.new_chat_started = True
    else:
        try:
            with open(f"chat_logs/{selected}.json", "r") as f:
                st.session_state.chat_history = json.load(f)
                st.session_state.chat_title = selected
                st.session_state.current_session = selected
            st.session_state.new_chat_started = False
        except FileNotFoundError:
            st.warning("Chat file not found.")

    if st.sidebar.button("🗑️ Clear all chat logs"):
        for f in log_files:
            os.remove(f"chat_logs/{f}")
        st.sidebar.success("All chats deleted. Refresh to start fresh.")
        st.stop()

    # ──────────────────────────────────────────────────────────────
    # 7) Chat Input Logic
    # ──────────────────────────────────────────────────────────────
    user_input = st.chat_input("Ask about building ops, CAD, or HVAC:")
    if user_input:
        question = user_input.strip()
        st.session_state.chat_history.append({"user": question})

        if not st.session_state.chat_title:
            title = generate_title_from_message(question)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            full_title = f"{timestamp}_{sanitize_filename(title)}"
            st.session_state.chat_title = full_title
            st.session_state.current_session = full_title
            st.session_state.new_chat_started = False

        if not is_domain_question(question):
            st.error("This assistant only answers questions about building ops, HVAC, or CAD.")
        else:
            try:
                context_lines = [line for line in pdf_text.split("\n") if is_relevant_content(line)]
                if context_lines:
                    context = "\n".join(context_lines[:50])
                    prompt = f"Use this document:\n\n{context}\n\nQuestion: {question}"
                    response = model.invoke([HumanMessage(content=prompt)])
                else:
                    response = model.invoke([HumanMessage(content=question)])
                bot_reply = getattr(response, "content", str(response))
                st.session_state.chat_history[-1]["bot"] = bot_reply
            except Exception as e:
                st.error("Model error:")
                st.exception(e)

    # ──────────────────────────────────────────────────────────────
    # 8) Save Chat & Display Messages
    # ──────────────────────────────────────────────────────────────
    if st.session_state.chat_history:
        try:
            title = st.session_state.chat_title or f"chat_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            st.session_state.chat_title = title
            with open(f"chat_logs/{title}.json", "w") as f:
                json.dump(st.session_state.chat_history, f, indent=2)
        except Exception as e:
            st.error(f"Failed to save chat: {e}")

        st.subheader(f"📘 Chat: {title.replace('_', ' ')}")
        for chat in st.session_state.chat_history:
            st.markdown(f"**You:** {chat['user']}")
            if "bot" in chat:
                st.markdown(f"**Bot:** {chat['bot']}")

    # Logout button at bottom
    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.rerun()
