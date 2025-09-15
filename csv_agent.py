# csv_agent.py
from __future__ import annotations

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent

import streamlit as st
import pandas as pd
import pdfplumber
import os
import json
import traceback

# ──────────────────────────────────────────────────────────────────────────────
# 0) Streamlit page + minimal debug info (renders even if something later fails)
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Elite CAD & Building Ops Chatbot", layout="wide")
st.title("🏗️ Elite CAD & Building Operations AI Chatbot")

with st.expander("Debug info (safe to collapse)"):
    st.write("CWD:", os.getcwd())
    st.write("Files:", os.listdir())

# ──────────────────────────────────────────────────────────────────────────────
# 1) API key loading: Heroku env first, then st.secrets for local dev
# ──────────────────────────────────────────────────────────────────────────────
openai_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
if not openai_key:
    st.error("❌ Missing OPENAI_API_KEY. Set it in **Heroku → Settings → Config Vars** "
             "(or in `.streamlit/secrets.toml` when running locally).")
    st.stop()

# ──────────────────────────────────────────────────────────────────────────────
# 2) Model
# ──────────────────────────────────────────────────────────────────────────────
try:
    model = ChatOpenAI(api_key=openai_key, model="gpt-4o")
except Exception as e:
    st.error("Failed to initialize ChatOpenAI:")
    st.exception(e)
    st.stop()

# ──────────────────────────────────────────────────────────────────────────────
# 3) Data loading with guards
# ──────────────────────────────────────────────────────────────────────────────
CSV_PATH = "PinConversation.csv"
if not os.path.exists(CSV_PATH):
    st.error(f"❌ CSV not found: `{CSV_PATH}`. Ensure it’s committed to the repo root "
             "with the exact same name/casing.")
    st.stop()

try:
    df = pd.read_csv(CSV_PATH).fillna(0)
except Exception as e:
    st.error("❌ Failed to read the CSV:")
    st.exception(e)
    st.stop()

# Ensure we have a text column to filter on
CONTENT_COL = None
for candidate in df.columns:
    c = str(candidate).lower()
    if c in {"content", "text", "message", "body", "notes"} or "content" in c or "text" in c:
        CONTENT_COL = candidate
        break

if CONTENT_COL is None:
    st.error("❌ Couldn’t find a text column in the CSV (e.g., 'content', 'text', 'message'). "
             "Please rename the appropriate column or update the code to point at it.")
    st.write("Columns found:", list(df.columns))
    st.stop()

st.write("### 📊 Dataset Preview")
st.dataframe(df.head(100))

# ──────────────────────────────────────────────────────────────────────────────
# 4) Domain filters
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
# 5) Optional PDF upload
# ──────────────────────────────────────────────────────────────────────────────
uploaded_pdfs = st.file_uploader(
    "Upload PDFs related to HVAC / MEP systems (optional):",
    type="pdf", accept_multiple_files=True
)
pdf_text = ""
if uploaded_pdfs:
    for up in uploaded_pdfs:
        st.success(f"✅ Loaded PDF: {up.name}")
        try:
            with pdfplumber.open(up) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        pdf_text += text + "\n"
        except Exception as e:
            st.warning(f"Couldn’t parse {up.name}: {e}")
else:
    st.info("📄 Tip: Upload HVAC/CAD PDFs to improve answers.")

# ──────────────────────────────────────────────────────────────────────────────
# 6) Chat
# ──────────────────────────────────────────────────────────────────────────────
# Load/restore chat history
if "chat_history" not in st.session_state:
    try:
        if os.path.exists("chat_history.json"):
            with open("chat_history.json", "r") as f:
                st.session_state.chat_history = json.load(f)
        else:
            st.session_state.chat_history = []
    except Exception:
        st.session_state.chat_history = []

user_input = st.chat_input("Ask about building operations, CAD, or HVAC:")
if user_input:
    question = user_input.strip()
    st.session_state.chat_history.append({"user": question})

    if not is_domain_question(question):
        st.error("❗ Only questions about building operations, CAD, and maintenance are supported.")
    else:
        # Filter dataset to relevant rows
        try:
            filtered_df = df[df[CONTENT_COL].apply(is_relevant_content)]
        except Exception as e:
            st.error("Failed while filtering the CSV:")
            st.exception(e)
            st.stop()

        pdf_snippets = [line for line in pdf_text.split("\n") if is_relevant_content(line)]
        agent_response = ""

        # Try dataframe agent first if we have relevant rows
        if not filtered_df.empty:
            try:
                agent = create_pandas_dataframe_agent(
                    llm=model,
                    df=filtered_df,
                    verbose=False,
                    allow_dangerous_code=True,
                    handle_parsing_errors=True,
                    max_iterations=20
                )
                QUERY = (
                    "You are a helpful assistant focused on building operations and mechanical systems. "
                    "Answer the question below using the dataset if possible. "
                    "If the dataset does not contain relevant info, say so clearly.\n\n"
                    f"Question: {question}"
                )
                res = agent.invoke(QUERY)
                agent_response = (res.get("output") or "").strip()
            except Exception as e:
                st.warning("⚠️ Dataframe agent failed; falling back to direct LLM.")

        # LLM fallback (with PDF context if available)
        if not agent_response or "no information" in agent_response.lower():
            try:
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
                st.error("❌ LLM call failed:")
                st.exception(e)
                final_response = ""
        else:
            final_response = agent_response

        if final_response:
            st.markdown(final_response)
            st.session_state.chat_history[-1]["bot"] = final_response

# Show history & (best-effort) persist to ephemeral FS
if st.session_state.get("chat_history"):
    st.write("### 💬 Conversation History")
    for chat in st.session_state.chat_history:
        st.markdown(f"**You:** {chat['user']}")
        if "bot" in chat:
            st.markdown(f"**Bot:** {chat['bot']}")
    try:
        with open("chat_history.json", "w") as f:
            json.dump(st.session_state.chat_history, f, indent=2)
    except Exception:
        pass
