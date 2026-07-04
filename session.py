import streamlit as st

def require_login():
    """Stop the page if user is not logged in."""
    if "user" not in st.session_state or st.session_state.user is None:
        st.warning("Please log in first.")
        st.stop()
      
def logout():
    """Clear current login session."""
    st.session_state.user = None
    st.session_state.login_error = None
    st.session_state.last_reset_password = None
    st.rerun()
