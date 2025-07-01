import streamlit as st
from streamlit_chat import message
from langchain.chains import ConversationalRetrievalChain
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.llms import CTransformers
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.memory import ConversationBufferMemory


# Function to load PDF documents
def load_documents():
    loader = DirectoryLoader('data/', glob="*.pdf", loader_cls=PyPDFLoader)
    documents = loader.load()
    return documents

# Function to split text into chunks
def split_text_into_chunks(documents):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    text_chunks = text_splitter.split_documents(documents)
    return text_chunks

# Function to create embeddings
def create_embeddings():
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2",
                                       model_kwargs={'device': 'cpu'})
    return embeddings

# Function to create vector store
def create_vector_store(text_chunks, embeddings):
    vector_store = FAISS.from_documents(text_chunks, embeddings)
    return vector_store

# Function to create LLM model
def create_llms_model():
    llm = CTransformers(model="mistral-7b-instruct-v0.1.Q4_K_M.gguf",
                        config={'max_new_tokens': 128, 'temperature': 0.01},
                        streaming=True)
    return llm


# Page Title and Styling
st.title("Elite CAD GPT")
st.title("Ask me anything")
st.markdown('<style>h1 { color: orange; text-align: center; }</style>', unsafe_allow_html=True)
st.subheader('Got it')
st.markdown('<style>h1 { color: pink; text-align: center; }</style>', unsafe_allow_html=True)

# Load documents
documents = load_documents()

# Split into chunks
text_chunks = split_text_into_chunks(documents)

# Create embeddings and vector store
embeddings = create_embeddings()
vector_store = create_vector_store(text_chunks, embeddings)

# Load the language model
llm = create_llms_model()

# Initialize session state
if 'history' not in st.session_state:
    st.session_state['history'] = []

if 'generated' not in st.session_state:
    st.session_state['generated'] = ["Hello, ask me anything about building operations."]

if 'past' not in st.session_state:
    st.session_state['past'] = ["Hey!"]

# Create memory
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# Create chain
chain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    chain_type='stuff',
    retriever=vector_store.as_retriever(),
    memory=memory
)

# Define chat function
def conversation_chat(query):
    result = chain({'question': query, "chat_history": st.session_state['history']})
    st.session_state['history'].append((query, result["answer"]))
    return result["answer"]

# UI containers
replay_container = st.container()
container = st.container()

with container:
    with st.form(key='my_form', clear_on_submit=True):
        user_input = st.text_input("Question", placeholder="Ask about building operations")
        submit_button = st.form_submit_button(label='Send')

    if submit_button and user_input:
        output = conversation_chat(user_input)
        st.session_state['past'].append(user_input)
        st.session_state['generated'].append(output)

# Display chat history
if st.session_state['generated']:
    with replay_container:
        for i in range(len(st.session_state['generated'])):
            message(st.session_state["past"][i], is_user=True, key=f'{i}_user', avatar_style="thumbs")
            message(st.session_state["generated"][i], key=str(i), avatar_style="fun_emoji")
