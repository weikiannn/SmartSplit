import streamlit as st
from utils.supabase import supabase


def send_otp(email: str):
    """Send login/signup OTP to email."""
    return supabase.auth.sign_in_with_otp({
        "email": email
    })


def verify_otp(email: str, token: str):
    """Verify OTP and return session."""
    return supabase.auth.verify_otp({
        "email": email,
        "token": token,
        "type": "email"
    })


def current_user():
    if "user" in st.session_state:
        return st.session_state.user
    return None


def logout():
    st.session_state.clear()