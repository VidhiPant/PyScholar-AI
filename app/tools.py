import smtplib
from email.message import EmailMessage
import sqlite3
import os
import streamlit as st # Import streamlit to access secrets

# --- 1. DATABASE TOOL ---
def save_booking_to_db(name, email, phone, booking_type, date, time):
    """
    Saves the booking details to the SQLite database.
    """
    # Force absolute path to ensure we hit the same DB as the dashboard
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, '..', 'db', 'bookings.db')
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Insert Customer (simple logic: insert new row even if email exists to avoid complex logic for now)
        c.execute("INSERT INTO customers (name, email, phone) VALUES (?, ?, ?)", (name, email, phone))
        customer_id = c.lastrowid
        
        # Insert Booking
        c.execute("INSERT INTO bookings (customer_id, booking_type, date, time, status) VALUES (?, ?, ?, ?, 'Confirmed')", 
                  (customer_id, booking_type, date, time))
        
        conn.commit()
        booking_id = c.lastrowid
        conn.close()
        return True, booking_id
    except Exception as e:
        return False, str(e)


# --- 2. REAL EMAIL TOOL (SMTP) ---
def send_confirmation_email(to_email, name, booking_details):
    """
    Sends a real email using credentials from Streamlit Secrets.
    """
    # ============================================================
    # 👇 LOAD CREDENTIALS SECURELY
    # ============================================================
    try:
        SENDER_EMAIL = st.secrets["email"]["sender_email"]
        APP_PASSWORD = st.secrets["email"]["app_password"]
    except Exception:
        st.error("❌ Email credentials missing! Check your .streamlit/secrets.toml")
        return False
    # ============================================================

    # Create the email content
    msg = EmailMessage()
    msg['Subject'] = f"✅ Session Confirmed: {name}"
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email  # <--- This uses whatever email the user provided in chat!
    
    msg.set_content(f"""
    Hello {name},

    Your mentorship session has been successfully booked!
    
    Here are your details:
    --------------------------------------------------
    {booking_details}
    --------------------------------------------------

    Please be ready 5 minutes before the scheduled time with your questions.

    Best regards,
    PyScholar AI Team
    """)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, APP_PASSWORD)
            smtp.send_message(msg)
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False