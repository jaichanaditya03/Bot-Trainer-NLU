"""
Authentication pages - Register and Login
"""
import re
from time import sleep
import streamlit as st
from api_client import api_post, humanize_error
from dataset_manager import load_persisted_dataset
from styles import ENTER_NAVIGATION_JS


def clear_session_data():
    """Clear all session data for fresh login"""
    st.session_state["dataset_df"] = None
    st.session_state["dataset_analysis"] = None
    st.session_state["evaluation_results"] = None
    st.session_state["uploaded_filename"] = None
    st.session_state["uploaded_history"] = []
    st.session_state["selected_dataset_checksum"] = None
    st.session_state["processed_upload_token"] = None


def render_register_page():
    """Render the registration page"""
    st.title("Create Account 🧾")
    st.markdown(ENTER_NAVIGATION_JS, unsafe_allow_html=True)

    username = st.text_input("👤 Username")
    email = st.text_input("📧 Email")
    password = st.text_input("🔐 Password", type="password")

    submitted = st.button("Register")

    if submitted:
        if not username or not email or not password:
            st.warning("⚠️ Please fill in all fields.")
        elif len(password) < 6 or not re.search(r"[^\w\s]", password):
            st.warning("⚠️ Password must be at least 6 characters and include a special character.")
        else:
            with st.spinner("Registering..."):
                payload = {
                    "username": username.strip(),
                    "email": email.strip(),
                    "password": password,
                }
                data, status = api_post("/register", json=payload)
                sleep(0.8)
                if status in (200, 201):
                    st.balloons()
                    st.success("✅ Registration successful! Redirecting to login...")
                    sleep(1)
                    st.session_state["page"] = "Login"
                    st.rerun()
                else:
                    st.error(f"❌ {humanize_error(data)}")


def render_login_page():
    """Render the login page"""
    st.title("Login 🔑")
    st.markdown(ENTER_NAVIGATION_JS, unsafe_allow_html=True)

    email = st.text_input("📧 Email", key="login_email")
    password = st.text_input("🔐 Password", type="password", key="login_pass")

    # Login button
    submitted = st.button("Login", use_container_width=True, type="primary")

    # Forgot Password link (aligned to right)
    col1, col2, col3 = st.columns([2, 1, 1])
    with col3:
        if st.button("Forgot Password?", key="forgot_pass_link"):
            st.session_state["page"] = "Forgot Password"
            st.rerun()

    if submitted:
        if not email or not password:
            st.warning("⚠️ Please fill in all fields.")
        else:
            with st.spinner("Verifying credentials..."):
                payload = {"email": email, "password": password}
                data, status = api_post("/login", json=payload)
                sleep(0.8)
                if status == 200:
                    # Clear any previous session data first
                    clear_session_data()
                    
                    # Set new user credentials
                    st.session_state["token"] = data.get("access_token")
                    st.session_state["email"] = email
                    st.session_state["username"] = data.get("username")
                    
                    # Load user's own dataset history
                    load_persisted_dataset(force=True)
                    
                    display_name = st.session_state["username"] or email
                    st.success(f"🎉 Welcome back, {display_name}")
                    sleep(1)
                    st.session_state["page"] = "Dashboard"
                    st.rerun()
                else:
                    st.error(f"❌ Login failed: {humanize_error(data)}")
