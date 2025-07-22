from langchain.adapters import openai
from langchain.schema import HumanMessage
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import pandas as pd
import streamlit as st

# Load environment variables
load_dotenv()
openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key:
    raise ValueError("OPENAI_API_KEY is not set!")

# Set up LLM
llm_name = "gpt-3.5-turbo"
model = ChatOpenAI(api_key=openai_key, model=llm_name)

# Load CSV
df = pd.read_csv("PinConversation.csv").fillna(value=0)

# Expanded domain keywords
ALLOWED_KEYWORDS = [
    "building", "construction", "cad", "design", "drafting", "maintenance", "hvac",
    "inspection", "roof", "electrical", "plumbing", "prototype", "mechanical",
    "facility", "repair", "renovation", "floor plan", "architectural", "engineering",
    "structural", "filter", "thermostat", "duct", "chiller", "boiler", "temperature",
    "energy", "airflow", "motor", "pump", "equipment", "safety", "code compliance",
    "circuit", "fuse", "wiring", "breaker", "water damage", "leak", "vibration"
]

def is_domain_question(question: str):
    q_lower = question.lower()
    return any(keyword in q_lower for keyword in ALLOWED_KEYWORDS)

def is_relevant_content(text: str):
    text_lower = str(text).lower()
    return any(keyword in text_lower for keyword in ALLOWED_KEYWORDS)

# Streamlit interface
st.title("Elite CAD & Building Operations AI Chatbot")

st.write("### Dataset Preview")
st.write(df.head(100))

st.write("### Ask a question")
question = st.text_input(
    "Ask me something related to building operations, CAD design, or mechanical maintenance:",
    "What are the most frequent mechanical problems?"
)

if st.button("Run Query"):
    if not is_domain_question(question):
        st.error("❗ Sorry, I can only answer questions related to building operations, CAD design, or maintenance tasks.")
    else:
        # Filter relevant data
        filtered_df = df[df["content"].apply(is_relevant_content)]

        from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent

        if not filtered_df.empty:
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
                "If the dataset does not contain relevant info, fall back to general knowledge.\n\n"
                f"Question: {question}"
            )

            try:
                res = agent.invoke(QUERY)
                agent_response = res["output"].strip()

                # If agent response doesn't answer the question well, fall back to LLM
                if not agent_response or "no information" in agent_response.lower() or "not found" in agent_response.lower():
                    st.warning("⚠️ Dataset does not contain useful information. Using general knowledge...")
                    response = model.invoke([HumanMessage(content=question)])
                    st.write("### General Answer")
                    st.markdown(response.content)
                else:
                    st.write("### Final Answer")
                    st.markdown(agent_response)

            except Exception as e:
                st.warning("⚠️ Dataset agent failed. Falling back to general knowledge.")
                try:
                    response = model.invoke([HumanMessage(content=question)])
                    st.write("### General Answer")
                    st.markdown(response.content)
                except Exception as e:
                    st.error(f"LLM fallback also failed: {e}")

        else:
            st.info("ℹ️ No relevant data in the dataset. Using general knowledge...")
            try:
                response = model.invoke([HumanMessage(content=question)])
                st.write("### General Answer")
                st.markdown(response.content)
            except Exception as e:
                st.error(f"LLM response failed: {e}")
