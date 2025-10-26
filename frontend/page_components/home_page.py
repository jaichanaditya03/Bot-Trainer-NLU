"""
Home page rendering
"""
import streamlit as st
from styles import ENTER_NAVIGATION_JS


def render_home_page():
    """Render the home/welcome page"""
    st.markdown(ENTER_NAVIGATION_JS, unsafe_allow_html=True)
    st.markdown(
        """
        <div class="hero-intro">
            <h1>Welcome to Bot Trainer Application 🤖</h1>
            <p>Design, launch, and manage conversational projects in a single secure workspace. Register or log in to start training bots tailored to your team.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cta_cols = st.columns(2)
    create_clicked = False
    login_clicked = False
    with cta_cols[0]:
        if st.button("Create an account", use_container_width=True):
            create_clicked = True
    with cta_cols[1]:
        if st.button("Access your workspace", use_container_width=True):
            login_clicked = True

    if create_clicked:
        st.session_state["page"] = "Register"
        st.rerun()
    if login_clicked:
        st.session_state["page"] = "Login"
        st.rerun()
