from pathlib import Path
import streamlit as st


def render_header(title="Student Attendance System", subtitle=None):
    logo_path = Path("assets/OIP.jpg")

    col_logo, col_title = st.columns([1, 8])

    with col_logo:
        if logo_path.exists():
            st.image(str(logo_path), width=90)

    with col_title:
        st.title(title)
        if subtitle:
            st.caption(subtitle)

    st.divider()
