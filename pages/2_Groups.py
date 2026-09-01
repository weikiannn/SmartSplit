import streamlit as st
from utils.supabase import supabase

if "user" not in st.session_state:
    st.switch_page("app.py")

user = st.session_state.user

st.set_page_config(page_title="Groups")

st.title("👥 Expense Groups")

# ---------------------------------------------------
# User Profile
# ---------------------------------------------------

profile = supabase.table("profiles") \
    .select("*") \
    .eq("id", user.id) \
    .execute().data[0]

st.write(f"### Welcome, {profile['nickname']}")

st.divider()

# ---------------------------------------------------
# Create Group
# ---------------------------------------------------

st.subheader("➕ Create New Group")

group_name = st.text_input("Group Name")

if st.button("Create Group"):

    if group_name.strip() == "":
        st.error("Group name required.")

    else:

        new_group = supabase.table("groups").insert({

            "name": group_name,

            "admin_id": user.id

        }).execute()

        group = new_group.data[0]

        supabase.table("group_members").insert({

            "group_id": group["id"],

            "user_id": user.id

        }).execute()

        st.success("Group created!")

st.divider()

# ---------------------------------------------------
# Join via Invite
# ---------------------------------------------------

if "invite_code" in st.session_state:

    invite = st.session_state.invite_code

    found = supabase.table("groups") \
        .select("*") \
        .eq("invite_code", invite) \
        .execute()

    if len(found.data) > 0:

        group = found.data[0]

        st.success(f"Invitation: {group['name']}")

        if st.button("Join This Group"):

            exist = supabase.table("group_members") \
                .select("*") \
                .eq("group_id", group["id"]) \
                .eq("user_id", user.id) \
                .execute()

            if len(exist.data) == 0:

                supabase.table("group_members").insert({

                    "group_id": group["id"],

                    "user_id": user.id

                }).execute()

            del st.session_state.invite_code

            st.success("Joined successfully!")

            st.rerun()

st.divider()

# ---------------------------------------------------
# My Groups
# ---------------------------------------------------

st.subheader("📂 My Groups")

memberships = supabase.table("group_members") \
    .select("group_id") \
    .eq("user_id", user.id) \
    .execute()

if len(memberships.data) == 0:

    st.info("No groups yet.")

else:

    for m in memberships.data:

        group = supabase.table("groups") \
            .select("*") \
            .eq("id", m["group_id"]) \
            .execute().data[0]

        with st.container(border=True):

            st.write(f"## {group['name']}")

            if group["admin_id"] == user.id:
                st.success("You are the Admin")
            else:
                st.caption("Member")

            invite_link = (
                "https://smartsplit.streamlit.app/"
                f"?join={group['invite_code']}"
            )

            st.text_input(
                "Invite Link",
                value=invite_link,
                key=group["id"],
                disabled=True
            )

            col1, col2 = st.columns(2)

            with col1:

                if st.button("Open", key=f"open_{group['id']}"):

                    st.session_state.current_group = group

                    st.switch_page("pages/3_Expenses.py")

            with col2:

                if st.button("Copy Link", key=f"copy_{group['id']}"):

                    st.toast("Copy the link above!")

# Inside each group after clicking Open
members = supabase.table("group_members") \
    .select("user_id, profiles(nickname)") \
    .eq("group_id", group["id"]) \
    .execute().data

for m in members:
    col1, col2 = st.columns([4,1])

    col1.write(m["profiles"]["nickname"])

    if group["admin_id"] == user.id and m["user_id"] != user.id:
        if col2.button("Remove", key=m["user_id"]):
            supabase.table("group_members") \
                .delete() \
                .eq("group_id", group["id"]) \
                .eq("user_id", m["user_id"]) \
                .execute()
            st.rerun()