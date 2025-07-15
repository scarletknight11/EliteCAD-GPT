from langchain.adapters import openai
from langchain.schema import HumanMessage, SystemMessage
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import pandas as pd
import streamlit as st

# Load environment variables from .env file
load_dotenv()

openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key:
    raise ValueError("OPENAI_API_KEY is not set in your .env file!")

llm_name = "gpt-3.5-turbo"
model = ChatOpenAI(api_key=openai_key, model=llm_name)

# Read CSV file
df = pd.read_csv("PinConversation.csv").fillna(value=0)

# Domain keywords
ALLOWED_KEYWORDS = [
    "building", "construction", "cad", "design", "drafting", "maintenance",
    "operations", "hvac", "inspection", "roof", "electrical", "plumbing",
    "prototype", "mechanical", "facility", "repair", "renovation", "floor plan",
    "architectural", "engineering", "structural"
]


def is_allowed_question(q):
    q_lower = q.lower()
    return any(keyword in q_lower for keyword in ALLOWED_KEYWORDS)


def is_relevant_content(text):
    text_lower = str(text).lower()
    return any(keyword in text_lower for keyword in ALLOWED_KEYWORDS)


# Streamlit UI
st.title("Elite CAD & Building Operations AI Chatbot")

st.write("### Dataset Preview")
st.write(df.head(100))

st.write("### Ask a question")
question = st.text_input(
    "Enter your question about the dataset (building/CAD/maintenance topics only):",
    "what is first text in the content column?"
)

if st.button("Run Query"):
    if is_allowed_question(question):
        # Filter CSV to only include relevant content rows
        filtered_df = df[df["content"].apply(is_relevant_content)]

        if filtered_df.empty:
            st.write("⚠️ No relevant building operations data found in the CSV.")
        else:
            # Create a new agent using only the filtered dataframe
            from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent

            agent = create_pandas_dataframe_agent(
                llm=model,
                df=filtered_df,
                verbose=True,
                allow_dangerous_code=True,
                handle_parsing_errors=True,
            )

            CSV_PROMPT_PREFIX = """
            First set the pandas display options to show all the columns,
            get the column names, then answer the question.
            """

            CSV_PROMPT_SUFFIX = """
            - **ALWAYS** before giving the Final Answer, try another method.
            Then reflect on the answers of the two methods you did and ask yourself
            if it answers correctly the original question.
            If you are not sure, try another method.
            FORMAT 4 FIGURES OR MORE WITH COMMAS.
            - If the methods tried do not give the same result, reflect and
            try again until you have two methods that have the same result.
            - If you still cannot arrive at a consistent result, say that
            you are not sure of the answer.
            - If you are sure of the correct answer, create a beautiful
            and thorough response using Markdown.
            - **DO NOT MAKE UP AN ANSWER OR USE PRIOR KNOWLEDGE,
            ONLY USE THE RESULTS OF THE CALCULATIONS YOU HAVE DONE**.
            - **ALWAYS**, as part of your "Final Answer", explain how you got
            to the answer on a section that starts with: "\n\nExplanation:\n".
            In the explanation, mention the column names that you used to get
            to the final answer.
            """

            QUERY = CSV_PROMPT_PREFIX + question + CSV_PROMPT_SUFFIX
            res = agent.invoke(QUERY)

            st.write("### Final Answer")
            st.markdown(res["output"])
    else:
        st.write(
            "❗ Sorry, I can only answer questions related to building operations, CAD design, or maintenance tasks.")
