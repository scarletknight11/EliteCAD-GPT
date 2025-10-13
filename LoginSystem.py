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
# SPLASH SCREEN FUNCTION (MP4 autoplay animation)
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
        }
        video {
            width: 70%;
            max-width: 800px;
            border-radius: 12px;
            outline: none;
            box-shadow: 0 0 25px rgba(0, 0, 0, 0.7);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    video_path = "Elite Animated Logo.mp4"  # Must exist in same folder
    try:
        # Embed HTML5 autoplay video directly
        video_html = f"""
        <div class="splash-container">
            <video autoplay muted playsinline>
                <source src="{video_path}" type="video/mp4">
                Your browser does not support the video tag.
            </video>
        </div>
        """
        st.markdown(video_html, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"❌ Error loading splash video: {e}")
        time.sleep(1)
        st.session_state.show_splash = False
        st.rerun()

    # Play animation for 3 seconds (adjust if your video is longer)
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
