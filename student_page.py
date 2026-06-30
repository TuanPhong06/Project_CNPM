import pandas as pd
import streamlit as st
from auth import change_password
from services.attendance_service import check_in, get_student_history


def render_student_page(user: dict):
    st.header("Student Dashboard")
    st.write(f"Welcome, **{user['full_name']}**")

    tab_checkin, tab_history, tab_account = st.tabs(
        ["Check Attendance", "Attendance History", "Account"]
    )

    with tab_checkin:
        st.subheader("Enter Attendance Session Code")
        session_code = st.text_input("Session code", placeholder="Example: 1N2001")
        if st.button("Check in", type="primary"):
            if not session_code.strip():
                st.warning("Please enter the attendance session code.")
            else:
                success, message = check_in(user["id"], session_code)
                if success:
                    st.success(message)
                else:
                    st.error(message)

    with tab_history:
        st.subheader("My Attendance History")
        history = get_student_history(user["id"])
        if history:
            st.dataframe(pd.DataFrame(history), use_container_width=True)
        else:
            st.info("No attendance history yet.")

    with tab_account:
        st.subheader("Change Password")
        old_password = st.text_input("Old password", type="password")
        new_password = st.text_input("New password", type="password")
        confirm_password = st.text_input("Confirm new password", type="password")

        if st.button("Update password"):
            if new_password != confirm_password:
                st.error("New password and confirmation do not match.")
            elif len(new_password) < 6:
                st.warning("Password must contain at least 6 characters.")
            elif change_password(user["id"], old_password, new_password):
                st.success("Password updated successfully.")
            else:
                st.error("Old password is incorrect.")
