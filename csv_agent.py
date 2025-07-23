from langchain.adapters import openai
from langchain.schema import HumanMessage
from langchain_openai import ChatOpenAI
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
import pandas as pd
import streamlit as st
import os
import pdfplumber
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()
openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key:
    raise ValueError("OPENAI_API_KEY is not set!")

# Set up LLM with GPT-4o
llm_name = "gpt-4o"
model = ChatOpenAI(api_key=openai_key, model=llm_name)

# Load CSV
df = pd.read_csv("PinConversation.csv").fillna(value=0)

# Domain keywords
ALLOWED_KEYWORDS = [
    "building", "construction", "cad", "design", "drafting", "maintenance", "hvac",
    "inspection", "roof", "electrical", "plumbing", "prototype", "mechanical",
    "facility", "repair", "renovation", "floor plan", "architectural", "engineering",
    "structural", "filter", "thermostat", "duct", "chiller", "boiler", "temperature",
    "energy", "airflow", "motor", "pump", "equipment", "safety", "code compliance",
    "circuit", "fuse", "wiring", "breaker", "water damage", "leak", "vibration"
]

def is_domain_question(question: str):
    return any(keyword in question.lower() for keyword in ALLOWED_KEYWORDS)

def is_relevant_content(text: str):
    return any(keyword in str(text).lower() for keyword in ALLOWED_KEYWORDS)

# Streamlit UI
st.set_page_config(page_title="Elite CAD & Building Ops Chatbot", layout="wide")
st.title("\U0001F3D7️ Elite CAD & Building Operations AI Chatbot")

# Load chat history from file if exists
if "chat_history" not in st.session_state:
    if os.path.exists("chat_history.json"):
        with open("chat_history.json", "r") as f:
            st.session_state.chat_history = json.load(f)
    else:
        st.session_state.chat_history = []

# PDF Upload
uploaded_pdfs = st.file_uploader("Upload PDFs related to HVAC / MEP systems:", type="pdf", accept_multiple_files=True)
pdf_text = ""
if uploaded_pdfs:
    for uploaded_pdf in uploaded_pdfs:
        st.success(f"✅ Loaded PDF: {uploaded_pdf.name}")
        with pdfplumber.open(uploaded_pdf) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    pdf_text += extracted + "\n"

# Show CSV Preview
st.write("### \U0001F4CA Dataset Preview")
st.write(df.head(100))

# Chat Input
user_input = st.chat_input("Ask something about building operations, CAD, or HVAC systems:")
if user_input:
    question = user_input
    st.session_state.chat_history.append({"user": question})

    if not is_domain_question(question):
        st.error("❗ Only questions about building operations, CAD, and maintenance are supported.")
    else:
        filtered_df = df[df["content"].apply(is_relevant_content)]

        agent_response = ""
        pdf_snippets = [para for para in pdf_text.split("\n") if is_relevant_content(para)]

        if not filtered_df.empty:
            try:
                agent = create_pandas_dataframe_agent(
                    llm=model,
                    df=filtered_df,
                    verbose=True,
                    allow_dangerous_code=True,
                    handle_parsing_errors=True,
                    max_iterations=20
                )

                QUERY = (
                    "You are a helpful assistant focused on building operations and mechanical systems. "
                    "Answer the question below using the dataset if possible. "
                    "If the dataset does not contain relevant info, fall back to PDF or general knowledge.\n\n"
                    f"Question: {question}"
                )
                res = agent.invoke(QUERY)
                agent_response = res["output"].strip()
            except Exception as e:
                st.warning("⚠️ Agent failed. Using LLM fallback...")

        if not agent_response or "no information" in agent_response.lower():
            if pdf_snippets:
                context = "\n".join(pdf_snippets[:50])
                prompt = f"Use this building operations reference to answer:\n\n{context}\n\nQuestion: {question}"
                response = model.invoke([HumanMessage(content=prompt)])
                final_response = response.content
                st.markdown(final_response)
            else:
                response = model.invoke([HumanMessage(content=question)])
                final_response = response.content
                st.markdown(final_response)
        else:
            final_response = agent_response
            st.markdown(final_response)

        st.session_state.chat_history[-1]["bot"] = final_response

# Display and Save Full Chat History
if st.session_state.chat_history:
    st.write("### 💬 Conversation History")
    for chat in st.session_state.chat_history:
        st.markdown(f"**You:** {chat['user']}")
        if "bot" in chat:
            st.markdown(f"**Bot:** {chat['bot']}")

    # Save chat history to file
    with open("chat_history.json", "w") as f:
        json.dump(st.session_state.chat_history, f, indent=2)