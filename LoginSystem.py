import streamlit as st
import pyrebase
import time
from csv_agent import app  # Import chatbot app

# ✅ Do NOT call st.set_page_config() here — handled in csv_agent.py

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

# Session state setup
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None
if "show_splash" not in st.session_state:
    st.session_state.show_splash = False

# ──────────────────────────────────────────────
# SPLASH SCREEN FUNCTION (GIF autoplay)
# ──────────────────────────────────────────────
def splash_screen():
    st.markdown(
        """
        <style>
        .splash-container {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            height: 100vh;
            background-color: black;
            animation: fadeIn 1s ease-in;
        }
        .splash-container img {
            width: 60%;
            max-width: 700px;
            border-radius: 12px;
            box-shadow: 0 0 25px rgba(0, 0, 0, 0.7);
        }
        @keyframes fadeIn {
            from {opacity: 0;}
            to {opacity: 1;}
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    gif_path = "AnimatedLogo.gif"  # Ensure exact filename and same folder
    try:
        st.markdown(f"""
        <div class="splash-container">
            <img src="{gif_path}" alt="Animated Logo">
        </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"❌ Error loading splash GIF: {e}")
        time.sleep(1)
        st.session_state.show_splash = False
        st.rerun()

    # Let the GIF animation play for 3 seconds before redirect
    time.sleep(3)
    st.session_state.show_splash = False
    st.rerun()

# ──────────────────────────────────────────────
# LOGIN PAGE
# ──────────────────────────────────────────────
def login_page():
    st.title("Welcome to EliteCAD GPT")

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
                st.info('Now log in using your new account.')
            except Exception as e:
                st.error(f"❌ {e}")

    elif choice == 'Login':
        if st.button('Login'):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user = user
                st.session_state.show_splash = True  # Show splash after login
                st.success("✅ Login successful!")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"❌ {e}")

# ──────────────────────────────────────────────
# ROUTING LOGIC
# ──────────────────────────────────────────────
if not st.session_state.logged_in:
    login_page()
elif st.session_state.show_splash:
    splash_screen()
else:
    app()  # Run chatbot
