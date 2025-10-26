
import streamlit as st
from config import PAGE_TITLE, PAGE_ICON, LAYOUT, SIDEBAR_STATE, LOGO_URL, LOGO_WIDTH
from styles import BACKGROUND_CSS
from utils import get_sidebar_toggle_state

# Import page renderers
from page_components.home_page import render_home_page
from page_components.auth_pages import render_register_page, render_login_page
from page_components.dashboard_page import render_dashboard_page
from page_components.forgot_password_page import render_forgot_password_page

# ---------------- PAGE CONFIGURATION ----------------
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=LAYOUT,
    initial_sidebar_state=SIDEBAR_STATE,
)

# Apply custom CSS
st.markdown(BACKGROUND_CSS, unsafe_allow_html=True)

# ---------------- SESSION STATE INITIALIZATION ----------------
if "token" not in st.session_state:
    st.session_state["token"] = None
if "email" not in st.session_state:
    st.session_state["email"] = None
if "username" not in st.session_state:
    st.session_state["username"] = None
if "page" not in st.session_state:
    st.session_state["page"] = "Home"
if "dataset_df" not in st.session_state:
    st.session_state["dataset_df"] = None
if "dataset_analysis" not in st.session_state:
    st.session_state["dataset_analysis"] = None
if "evaluation_results" not in st.session_state:
    st.session_state["evaluation_results"] = None
if "uploaded_filename" not in st.session_state:
    st.session_state["uploaded_filename"] = None
if "uploaded_history" not in st.session_state:
    st.session_state["uploaded_history"] = []
if "selected_dataset_checksum" not in st.session_state:
    st.session_state["selected_dataset_checksum"] = None
if "processed_upload_token" not in st.session_state:
    st.session_state["processed_upload_token"] = None


# ---------------- HELPER FUNCTIONS ----------------
def set_page(page: str):
    """Set the current page"""
    st.session_state["page"] = page


def nav_options():
    """Get navigation options based on authentication state"""
    if st.session_state.get("token"):
        return ["Home", "Dashboard", "Logout"]
    return ["Home", "Register", "Login"]


# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.image(LOGO_URL, width=LOGO_WIDTH)
    st.markdown("###  Bot Trainer App")
    options = nav_options()
    current_page = st.session_state.get("page", options[0])
    
    # If current page is not in sidebar options (like Forgot Password), 
    # don't reset it, just show the closest option
    if current_page not in options:
        if current_page == "Forgot Password":
            # Keep on Forgot Password page, but show Login as selected in sidebar
            display_page = "Login"
        else:
            current_page = options[0]
            display_page = current_page
    else:
        display_page = current_page
    
    menu = st.radio(
        "Navigate",
        options,
        index=options.index(display_page),
        key="nav_menu",
    )
    
    # Only change page if user actively clicked a different menu item
    # Don't override programmatic page changes (like going to Forgot Password)
    if menu != st.session_state.get("page") and st.session_state.get("page") in options:
        set_page(menu)

# ---------------- MAIN CONTENT ROUTING ----------------
page = st.session_state.get("page", "Home")
sidebar_state = get_sidebar_toggle_state()

if page == "Home":
    render_home_page()

elif page == "Register":
    render_register_page()

elif page == "Login":
    render_login_page()

elif page == "Forgot Password":
    render_forgot_password_page()

elif page == "Dashboard":
    render_dashboard_page()

elif page == "Logout":
    # Clear session state - including all dataset history
    st.session_state["token"] = None
    st.session_state["email"] = None
    st.session_state["username"] = None
    st.session_state["dataset_df"] = None
    st.session_state["dataset_analysis"] = None
    st.session_state["evaluation_results"] = None
    st.session_state["uploaded_filename"] = None
    st.session_state["uploaded_history"] = []
    st.session_state["selected_dataset_checksum"] = None
    st.session_state["processed_upload_token"] = None
    set_page("Home")
    st.success(" You have been logged out successfully.")
    from time import sleep
    sleep(1)
    st.rerun()
