import streamlit as st

def current_user():
    return st.session_state.get("user", None)

def logout():
    st.session_state.clear()