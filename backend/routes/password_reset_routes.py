"""
Password reset routes - forgot password with OTP verification
"""
from fastapi import APIRouter, HTTPException, status
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from models import RegisterRequest
from auth import hash_password
from database import users_col, db

router = APIRouter()

# Temporary OTP storage collection
otp_col = db["password_reset_otps"]


class ForgotPasswordRequest(BaseModel):
    """Request OTP for password reset"""
    email: EmailStr


class VerifyOTPRequest(BaseModel):
    """Verify OTP"""
    email: EmailStr
    otp: str


class ResetPasswordRequest(BaseModel):
    """Reset password with verified OTP"""
    email: EmailStr
    otp: str
    new_password: str
    confirm_password: str


def send_otp_email(email: str, otp: str):
    """Send OTP to user's email"""
    try:
        # Email configuration from environment variables
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        sender_email = os.getenv("SENDER_EMAIL", "")
        sender_password = os.getenv("SENDER_PASSWORD", "")
        
        if not sender_email or not sender_password:
            # For development: just log the OTP
            print(f"[DEV MODE] OTP for {email}: {otp}")
            return True
        
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = "Password Reset OTP - Bot Trainer"
        message["From"] = sender_email
        message["To"] = email
        
        # Email body
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #32f47a;">Bot Trainer - Password Reset</h2>
                <p>You requested to reset your password.</p>
                <p>Your OTP (One-Time Password) is:</p>
                <h1 style="color: #2bf06f; letter-spacing: 5px;">{otp}</h1>
                <p>This OTP is valid for 10 minutes.</p>
                <p>If you didn't request this, please ignore this email.</p>
                <hr>
                <p style="color: #666; font-size: 12px;">Bot Trainer Application</p>
            </body>
        </html>
        """
        
        part = MIMEText(html, "html")
        message.attach(part)
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(message)
        
        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        # For development, still return True
        return True


@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest):
    """Send OTP to user's email for password reset"""
    # Check if user exists
    user = users_col.find_one({"email": data.email})
    if not user:
        raise HTTPException(status_code=404, detail="Email not registered")
    
    # Generate 6-digit OTP
    otp = str(random.randint(100000, 999999))
    
    # Store OTP in database with expiry (10 minutes)
    otp_col.update_one(
        {"email": data.email},
        {
            "$set": {
                "email": data.email,
                "otp": otp,
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(minutes=10),
                "verified": False
            }
        },
        upsert=True
    )
    
    # Send OTP via email
    send_otp_email(data.email, otp)
    
    return {
        "message": "OTP sent to your email",
        "email": data.email
    }


@router.post("/verify-otp")
def verify_otp(data: VerifyOTPRequest):
    """Verify OTP for password reset"""
    # Find OTP record
    otp_record = otp_col.find_one({"email": data.email})
    
    if not otp_record:
        raise HTTPException(status_code=404, detail="No OTP found for this email")
    
    # Check if OTP is expired
    if datetime.utcnow() > otp_record["expires_at"]:
        raise HTTPException(status_code=400, detail="OTP has expired. Please request a new one.")
    
    # Verify OTP
    if otp_record["otp"] != data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    # Mark OTP as verified
    otp_col.update_one(
        {"email": data.email},
        {"$set": {"verified": True}}
    )
    
    return {"message": "OTP verified successfully"}


@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest):
    """Reset password after OTP verification"""
    # Find OTP record
    otp_record = otp_col.find_one({"email": data.email})
    
    if not otp_record:
        raise HTTPException(status_code=404, detail="No OTP found for this email")
    
    # Check if OTP is verified
    if not otp_record.get("verified"):
        raise HTTPException(status_code=400, detail="OTP not verified")
    
    # Check if OTP is expired
    if datetime.utcnow() > otp_record["expires_at"]:
        raise HTTPException(status_code=400, detail="OTP has expired. Please request a new one.")
    
    # Verify OTP again
    if otp_record["otp"] != data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    # Check if passwords match
    if data.new_password != data.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    
    # Validate password strength
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    # Hash new password
    hashed = hash_password(data.new_password)
    
    # Update user password
    result = users_col.update_one(
        {"email": data.email},
        {"$set": {"password": hashed, "password_updated_at": datetime.utcnow()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Delete OTP record
    otp_col.delete_one({"email": data.email})
    
    return {"message": "Password reset successfully"}
