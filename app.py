import streamlit as st
from utils.auth import send_otp, verify_otp

st.set_page_config(
    page_title="Expense Splitter",
    page_icon="💸",
    layout="centered"
)

# Detect invite link
params = st.query_params

if "join" in params:
    st.session_state.invite_code = params["join"]

st.title("💸 Expense Splitter")

st.write("Login or sign up using Email OTP.")

tab1, tab2 = st.tabs(["Send OTP", "Verify OTP"])

with tab1:

    email = st.text_input("Email Address")

    if st.button("Send OTP", use_container_width=True):

        if email.strip() == "":
            st.error("Enter your email.")
        else:
            send_otp(email)
            st.success("OTP has been sent to your email.")

with tab2:

    verify_email = st.text_input("Email", key="verify_email")

    otp = st.text_input(
        "6-digit OTP",
        max_chars=6
    )

    if st.button("Login", use_container_width=True):

        try:
            session = verify_otp(verify_email, otp)

            st.session_state.user = session.user

            st.success("Login successful!")

            st.switch_page("pages/1_Profile.py")

        except Exception:
            st.error("Invalid OTP.")