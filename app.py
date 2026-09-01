import streamlit as st
from utils.supabase import supabase

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

tab1, tab2 = st.tabs(["Login", "Sign Up"])

# ---------------------------------------------------
# Tab 1: Existing User Login
# ---------------------------------------------------
with tab1:
    email_login = st.text_input("Email Address", key="login_email")

    if st.button("Log In", use_container_width=True, type="primary"):
        clean_email = email_login.strip().lower()

        if not clean_email:
            st.error("Please enter your email.")
        else:
            response = supabase.table("profiles") \
                .select("*") \
                .eq("email", clean_email) \
                .execute()

            if len(response.data) > 0:
                user_profile = response.data[0]
                st.session_state.user = st.types.SimpleNamespace(
                    id=user_profile["id"],
                    email=user_profile["email"],
                    nickname=user_profile["nickname"]
                )
                st.success("Login successful!")
                st.switch_page("pages/2_Groups.py")
            else:
                st.error("No account found with this email. Please sign up.")

# ---------------------------------------------------
# Tab 2: New User Sign Up
# ---------------------------------------------------
with tab2:
    email_signup = st.text_input("Email Address", key="signup_email")

    if "signup_stage" not in st.session_state:
        st.session_state.signup_stage = "enter_email"

    if st.button("Next", use_container_width=True):
        clean_email = email_signup.strip().lower()

        if not clean_email:
            st.error("Please enter an email address.")
        else:
            existing = supabase.table("profiles") \
                .select("id") \
                .eq("email", clean_email) \
                .execute()

            if len(existing.data) > 0:
                st.error("Account already exists. Please log in.")
            else:
                st.session_state.pending_email = clean_email
                st.session_state.signup_stage = "enter_nickname"

    if st.session_state.get("signup_stage") == "enter_nickname":
        st.divider()
        st.info(f"Signing up with: **{st.session_state.pending_email}**")
        nickname = st.text_input("Nickname", key="signup_nickname")

        if st.button("Complete Sign Up", use_container_width=True, type="primary"):
            clean_nick = nickname.strip()
            if not clean_nick:
                st.error("Please enter a nickname.")
            else:
                try:
                    res = supabase.table("profiles").insert({
                        "email": st.session_state.pending_email,
                        "nickname": clean_nick
                    }).execute()

                    new_user = res.data[0]

                    st.session_state.user = st.types.SimpleNamespace(
                        id=new_user["id"],
                        email=new_user["email"],
                        nickname=new_user["nickname"]
                    )

                    del st.session_state.signup_stage
                    del st.session_state.pending_email

                    st.success("Account created successfully!")
                    st.switch_page("pages/2_Groups.py")
                except Exception as e:
                    st.error(f"Sign up failed: {e}")