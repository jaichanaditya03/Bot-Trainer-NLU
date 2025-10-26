"""
Forgot Password Page - OTP-based password reset flow
"""
import streamlit as st
from api_client import api_post, humanize_error


def render_forgot_password_page():
    """Render the forgot password page with OTP verification"""
    st.title("🔐 Reset Your Password")
    
    # Initialize session state for forgot password flow
    if "fp_step" not in st.session_state:
        st.session_state["fp_step"] = "email"  # email, otp, reset
    if "fp_email" not in st.session_state:
        st.session_state["fp_email"] = ""
    if "fp_otp" not in st.session_state:
        st.session_state["fp_otp"] = ""
    
    # Step 1: Enter Email
    if st.session_state["fp_step"] == "email":
        render_email_step()
    
    # Step 2: Verify OTP
    elif st.session_state["fp_step"] == "otp":
        render_otp_step()
    
    # Step 3: Reset Password
    elif st.session_state["fp_step"] == "reset":
        render_reset_step()


def render_email_step():
    """Step 1: Request OTP via email"""
    st.markdown("### Step 1: Enter Your Email")
    st.info("📧 Enter your registered email address to receive an OTP")
    
    email = st.text_input(
        "Email Address",
        placeholder="your.email@example.com",
        key="fp_email_input"
    )
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("📨 Get OTP", use_container_width=True, type="primary"):
            if not email:
                st.error("⚠️ Please enter your email address")
                return
            
            if "@" not in email or "." not in email:
                st.error("⚠️ Please enter a valid email address")
                return
            
            with st.spinner("Sending OTP..."):
                data, status = api_post("/forgot-password", {"email": email})
                
                if status == 200:
                    st.session_state["fp_email"] = email
                    st.session_state["fp_step"] = "otp"
                    st.success(f"✅ {data.get('message', 'OTP sent to your email')}")
                    st.rerun()
                else:
                    st.error(f"❌ {humanize_error(data)}")
    
    with col2:
        if st.button("← Back to Login", use_container_width=True):
            reset_forgot_password_flow()
            st.session_state["page"] = "Login"
            st.rerun()


def render_otp_step():
    """Step 2: Verify OTP"""
    st.markdown("### Step 2: Verify OTP")
    st.info(f"📧 OTP has been sent to **{st.session_state['fp_email']}**")
    st.caption("⏱️ OTP is valid for 10 minutes")
    
    otp = st.text_input(
        "Enter OTP",
        placeholder="Enter 6-digit OTP",
        max_chars=6,
        key="fp_otp_input"
    )
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("✅ Verify OTP", use_container_width=True, type="primary"):
            if not otp:
                st.error("⚠️ Please enter the OTP")
                return
            
            if len(otp) != 6 or not otp.isdigit():
                st.error("⚠️ OTP must be 6 digits")
                return
            
            with st.spinner("Verifying OTP..."):
                data, status = api_post("/verify-otp", {
                    "email": st.session_state["fp_email"],
                    "otp": otp
                })
                
                if status == 200:
                    st.session_state["fp_otp"] = otp
                    st.session_state["fp_step"] = "reset"
                    st.success("✅ OTP verified successfully!")
                    st.rerun()
                else:
                    st.error(f"❌ {humanize_error(data)}")
    
    with col2:
        if st.button("🔄 Resend OTP", use_container_width=True):
            with st.spinner("Resending OTP..."):
                data, status = api_post("/forgot-password", {
                    "email": st.session_state["fp_email"]
                })
                
                if status == 200:
                    st.success("✅ OTP resent successfully!")
                else:
                    st.error(f"❌ {humanize_error(data)}")
    
    with col3:
        if st.button("← Back", use_container_width=True):
            st.session_state["fp_step"] = "email"
            st.rerun()


def render_reset_step():
    """Step 3: Set new password"""
    st.markdown("### Step 3: Set New Password")
    st.success("✅ OTP verified! Now set your new password")
    
    new_password = st.text_input(
        "New Password",
        type="password",
        placeholder="Enter new password (min 6 characters)",
        key="fp_new_password"
    )
    
    confirm_password = st.text_input(
        "Confirm Password",
        type="password",
        placeholder="Re-enter new password",
        key="fp_confirm_password"
    )
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("🔒 Reset Password", use_container_width=True, type="primary"):
            if not new_password or not confirm_password:
                st.error("⚠️ Please fill in both password fields")
                return
            
            if len(new_password) < 6:
                st.error("⚠️ Password must be at least 6 characters")
                return
            
            if new_password != confirm_password:
                st.error("⚠️ Passwords do not match")
                return
            
            with st.spinner("Resetting password..."):
                data, status = api_post("/reset-password", {
                    "email": st.session_state["fp_email"],
                    "otp": st.session_state["fp_otp"],
                    "new_password": new_password,
                    "confirm_password": confirm_password
                })
                
                if status == 200:
                    st.success("✅ Password reset successfully!")
                    st.balloons()
                    st.info("🔄 Redirecting to login page...")
                    
                    # Reset forgot password flow
                    reset_forgot_password_flow()
                    
                    # Redirect to login
                    from time import sleep
                    sleep(2)
                    st.session_state["page"] = "Login"
                    st.rerun()
                else:
                    st.error(f"❌ {humanize_error(data)}")
    
    with col2:
        if st.button("← Back", use_container_width=True):
            st.session_state["fp_step"] = "otp"
            st.rerun()


def reset_forgot_password_flow():
    """Reset the forgot password flow state"""
    st.session_state["fp_step"] = "email"
    st.session_state["fp_email"] = ""
    st.session_state["fp_otp"] = ""
