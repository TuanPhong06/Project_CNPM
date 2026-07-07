import streamlit as st


def logout():
    st.session_state.user = None
    st.rerun()
