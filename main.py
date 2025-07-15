import streamlit as st
from langchain.chat_models import ChatOpenAI
from dotenv import load_dotenv
import os
import pandas as pd
import json


def main():
    load_dotenv()

    st.set_page_config(page_title="Ask your CSV")
    st.header("Ask your CSV")

    # Initialize chat history
    if "history" not in st.session_state:
        st.session_state.history = []

    user_csv = st.file_uploader("Upload your CSV file", type="csv")

    if user_csv is not None:
        df = pd.read_csv(user_csv)

        st.write("CSV preview:")
        st.dataframe(df)

        # Select row number
        row_num = st.number_input("Select row number to extract text from (starting at 0):", min_value=0, max_value=len(df)-1, step=1)

        # Extract text from content column
        try:
            row_content = df.loc[row_num, "content"]
            parsed_json = json.loads(row_content)
            extracted_text = parsed_json["segments"][0]["text"]
            st.write("✅ **Extracted text from selected row:**")
            st.write(extracted_text)
        except Exception as e:
            st.error(f"Error parsing JSON or extracting text: {e}")
            extracted_text = None

        # Optional: ask LLM about this extracted text
        if extracted_text:
            user_question = st.text_area("Ask a question about this extracted text:")

            if user_question:
                llm = ChatOpenAI(
                    temperature=0,
                    model="gpt-4o",
                    openai_api_key=os.getenv("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")  # ← Use .env key
                )

                prompt = (
                    f"Here is the extracted text:\n\"{extracted_text}\"\n\n"
                    f"Question: {user_question}\n"
                    f"Please provide a short, clear answer."
                )

                response = llm.invoke(prompt)

                # Store in history
                st.session_state.history.append((user_question, response.content))

                st.write("Answer:")
                st.write(response.content)

    # Display chat history
    if st.session_state.history:
        st.write("---")
        st.write("### Chat History")
        for i, (q, a) in enumerate(st.session_state.history):
            st.markdown(f"**Q{i+1}:** {q}")
            st.markdown(f"**A{i+1}:** {a}")

if __name__ == "__main__":
    main()
