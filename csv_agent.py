from __future__ import annotations

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

import streamlit as st
import pdfplumber
import os
import json
import traceback
import datetime

# ──────────────────────────────────────────────────────────────────────────────
# 0) Streamlit Setup
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Elite CAD & Building Ops Chatbot", layout="wide")

# Company Logo (Replace with your actual file name)
st.image("EliteLogo.jpg", width=180)  # e.g. "elite_logo.png"

st.title("Elite CAD & Building Operations AI Chatbot")

# Create a folder to store all chat logs
os.makedirs("chat_logs", exist_ok=True)

# Create a unique chat session ID for each new session
session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
chat_log_path = f"chat_logs/chat_{session_id}.json"

# ──────────────────────────────────────────────────────────────────────────────
# 1) API Key Setup
# ──────────────────────────────────────────────────────────────────────────────
openai_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
if not openai_key:
    st.error("Missing OPENAI_API_KEY. Set it in Heroku → Settings → Config Vars "
             "(or in `.streamlit/secrets.toml` when running locally).")
    st.stop()

# ──────────────────────────────────────────────────────────────────────────────
# 2) Model Initialization
# ──────────────────────────────────────────────────────────────────────────────
try:
    model = ChatOpenAI(api_key=openai_key, model="gpt-4o")
except Exception as e:
    st.error("Failed to initialize ChatOpenAI:")
    st.exception(e)
    st.stop()

# ──────────────────────────────────────────────────────────────────────────────
# 3) Keywords for domain-restricted Q&A
# ──────────────────────────────────────────────────────────────────────────────
ALLOWED_KEYWORDS = [
    "building", "construction", "cad", "design", "drafting", "maintenance", "hvac",
    "inspection", "roof", "electrical", "plumbing", "prototype", "mechanical",
    "facility", "repair", "renovation", "floor plan", "architectural", "engineering",
    "structural", "filter", "thermostat", "duct", "chiller", "boiler", "temperature",
    "energy", "airflow", "motor", "pump", "equipment", "safety", "code compliance",
    "circuit", "fuse", "wiring", "breaker", "water damage", "leak", "vibration"
]

def is_domain_question(question: str) -> bool:
    q = (question or "").lower()
    return any(k in q for k in ALLOWED_KEYWORDS)

def is_relevant_content(val) -> bool:
    t = str(val).lower()
    return any(k in t for k in ALLOWED_KEYWORDS)

# ──────────────────────────────────────────────────────────────────────────────
# 4) PDF Upload
# ──────────────────────────────────────────────────────────────────────────────
uploaded_pdfs = st.file_uploader(
    "Upload HVAC / CAD PDFs (optional):", type="pdf", accept_multiple_files=True
)
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

# ──────────────────────────────────────────────────────────────────────────────
# 5) Chat State Initialization (Always Fresh on Launch)
# ──────────────────────────────────────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ──────────────────────────────────────────────────────────────────────────────
# 6) Sidebar Options: Load Old Logs / Clear Logs
# ──────────────────────────────────────────────────────────────────────────────
st.sidebar.header("Chat History Options")

# Load and preview old chat history
log_files = sorted(os.listdir("chat_logs"), reverse=True)
selected_log = st.sidebar.selectbox("Preview previous chat sessions:", ["None"] + log_files)
if selected_log != "None":
    try:
        with open(f"chat_logs/{selected_log}", "r") as f:
            prev_log = json.load(f)
        st.sidebar.markdown("---")
        st.sidebar.subheader("Previous Chat")
        for item in prev_log:
            st.sidebar.markdown(f"**You:** {item['user']}")
            if "bot" in item:
                st.sidebar.markdown(f"**Bot:** {item['bot']}")
    except Exception as e:
        st.sidebar.error(f"Error loading {selected_log}: {e}")

# Clear all chat logs
if st.sidebar.button("Clear all chat logs"):
    for f in log_files:
        os.remove(f"chat_logs/{f}")
    st.sidebar.success("All chat logs cleared.")

# ──────────────────────────────────────────────────────────────────────────────
# 7) Chat Input / LLM Response
# ──────────────────────────────────────────────────────────────────────────────
user_input = st.chat_input("Ask about building ops, CAD, or HVAC:")
if user_input:
    question = user_input.strip()
    st.session_state.chat_history.append({"user": question})

    if not is_domain_question(question):
        st.error("Only questions about building operations, CAD, and maintenance are supported.")
    else:
        try:
            pdf_snippets = [line for line in pdf_text.split("\n") if is_relevant_content(line)]
            if pdf_snippets:
                context = "\n".join(pdf_snippets[:50])
                prompt = (
                    "Use this building operations reference to answer:\n\n"
                    f"{context}\n\nQuestion: {question}"
                )
                response = model.invoke([HumanMessage(content=prompt)])
            else:
                response = model.invoke([HumanMessage(content=question)])
            final_response = getattr(response, "content", str(response))
        except Exception as e:
            st.error("LLM call failed:")
            st.exception(e)
            final_response = ""

        if final_response:
            st.markdown(final_response)
            st.session_state.chat_history[-1]["bot"] = final_response

# ──────────────────────────────────────────────────────────────────────────────
# 8) Save current chat session to file
# ──────────────────────────────────────────────────────────────────────────────
if st.session_state.get("chat_history"):
    try:
        with open(chat_log_path, "w") as f:
            json.dump(st.session_state.chat_history, f, indent=2)
    except Exception as e:
        st.error(f"Failed to save chat: {e}")

    st.write("Live Chat History")
    for chat in st.session_state.chat_history:
        st.markdown(f"**You:** {chat['user']}")
        if "bot" in chat:
            st.markdown(f"**Bot:** {chat['bot']}")
