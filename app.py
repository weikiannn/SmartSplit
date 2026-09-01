import streamlit as st
from utils.auth import guest_login

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

st.write("Enter your name to join and split expenses instantly.")

display_name = st.text_input("Your Name / Nickname", placeholder="e.g. Alice")

if st.button("Start Splitting", use_container_width=True, type="primary"):
    if display_name.strip() == "":
        st.error("Please enter a name.")
    else:
        # Save session and proceed
        guest_login(display_name.strip())
        st.success(f"Welcome, {display_name}!")
        st.switch_page("pages/1_Profile.py")