import streamlit as st
from utils.supabase import supabase


def guest_login(display_name: str):
    """Logs in a user anonymously using Supabase anonymous auth or a display name session."""
    # Create or update guest identity in session state
    st.session_state.user = {
        "email": f"{display_name.lower().replace(' ', '_')}@guest.local",
        "user_metadata": {"display_name": display_name}
    }
    
    # Try Supabase anonymous sign-in if enabled in your project
    try:
        res = supabase.auth.sign_in_anonymously({
            "options": {
                "data": {"display_name": display_name}
            }
        })
        if res and res.user:
            st.session_state.user = res.user
    except Exception:
        # Fallback to local session state if Supabase anonymous auth is disabled
        pass

    return st.session_state.user


def current_user():
    """Returns the current logged in user from session state."""
    if "user" in st.session_state:
        return st.session_state.user
    return None


def logout():
    """Clears the session and logs out."""
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    st.session_state.clear()