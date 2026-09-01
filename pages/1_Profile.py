import streamlit as st
from utils.supabase import supabase
from utils.auth import logout

if "user" not in st.session_state:
    st.switch_page("app.py")

user = st.session_state.user

st.set_page_config(page_title="Profile")

st.title("👤 My Profile")

profile = supabase.table("profiles") \
    .select("*") \
    .eq("id", user.id) \
    .execute()

# ---------------------------------------------------
# New User
# ---------------------------------------------------

if len(profile.data) == 0:

    st.info("Welcome! Create your profile first.")

    nickname = st.text_input("Nickname")

    if st.button("Create Profile", use_container_width=True):

        if nickname.strip() == "":
            st.error("Nickname cannot be empty.")
        else:

            supabase.table("profiles").insert({

                "id": user.id,

                "email": user.email,

                "nickname": nickname.strip()

            }).execute()

            st.success("Profile created!")

            st.switch_page("pages/2_Groups.py")

# ---------------------------------------------------
# Existing User
# ---------------------------------------------------

else:

    profile = profile.data[0]

    st.write(f"**Email:** {profile['email']}")

    nickname = st.text_input(
        "Nickname",
        value=profile["nickname"]
    )

    col1, col2 = st.columns(2)

    with col1:

        if st.button("Update Nickname", use_container_width=True):

            supabase.table("profiles") \
                .update({
                    "nickname": nickname.strip()
                }) \
                .eq("id", user.id) \
                .execute()

            st.success("Updated!")

    with col2:

        if st.button("Go To Groups", use_container_width=True):

            st.switch_page("pages/2_Groups.py")

st.divider()

if st.button("Logout"):

    logout()

    st.switch_page("app.py")