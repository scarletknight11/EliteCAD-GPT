import streamlit as st
import pyrebase

# Firebase config
firebaseConfig = {
    'apiKey': "AIzaSyCOEUNCKSh3AC2kwpOOoO1fGJvNdn7LI2M",
    'authDomain': "elitecadgpt.firebaseapp.com",
    'databaseURL': "https://elitecadgpt-default-rtdb.firebaseio.com",
    'projectId': "elitecadgpt",
    'storageBucket': "elitecadgpt.firebasestorage.app",
    'messagingSenderId': "314973084735",
    'appId': "1:314973084735:web:11a607c5228acb11a4ac8a",
    'measurementId': "G-ZL7TKS4G4P"
}

# Initialize Firebase
firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()
db = firebase.database()

st.set_page_config(page_title="EliteCAD GPT", layout="wide")
st.title("Welcome to EliteCAD GPT")

# Session state to track login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    choice = st.selectbox('Login / Signup', ['Login', 'Sign up'])
    email = st.text_input('Email')
    password = st.text_input('Password', type='password')

    if choice == 'Sign up':
        handle = st.text_input('Choose a username', value="Default")
        if st.button('Create my account'):
            try:
                user = auth.create_user_with_email_and_password(email, password)
                st.success('✅ Account created successfully!')
                auth.sign_in_with_email_and_password(email, password)
                db.child(user['localId']).child("Handle").set(handle)
                db.child(user['localId']).child("ID").set(user['localId'])
                st.info('Now go to Login to sign in.')
            except Exception as e:
                st.error(f"❌ {e}")

    elif choice == 'Login':
        if st.button('Login'):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user = user
                st.rerun()  # ✅ correct method
            except Exception as e:
                st.error(f"❌ {e}")

# --- MAIN APP VIEW ---
else:
    from csv_agent import app
    app()
