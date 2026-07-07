from pathlib import Path
import streamlit as st
from auth import login, reset_password, change_password, update_profile
from database import init_db
from app_pages.admin_page import render_admin_page
from app_pages.lecturer_page import render_lecturer_page
from app_pages.reports_page import render_reports_page
from app_pages.student_page import render_student_page
from seed_data import seed_if_empty
from utils.header import render_header
from utils.session import logout
from utils.header import render_header

logo_path = Path("assets/OIP.jpg")

st.set_page_config(
    page_title="Student Attendance System",
    page_icon=str(logo_path),
    layout="wide",
)

init_db()
seed_if_empty()

if "user" not in st.session_state:
    st.session_state.user = None
if "login_failures" not in st.session_state:
    st.session_state.login_failures = 0
if "captcha_answer" not in st.session_state:
    st.session_state.captcha_answer = "5"


def display_name(user: dict):
    return user.get("full_name") or user.get("fullname") or user.get("username") or "User"


def refresh_current_user():
    user = st.session_state.user
    if user:
        st.session_state.user = {**user}


def render_login_page():
    render_header("Student Attendance System", "Please log in to continue")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login", type="primary")

    if submitted:
        if st.session_state.login_failures >= 5:
            st.error("Too many failed attempts. Please refresh the page or try again later.")
        else:
            user = login(username, password)
            if user:
                st.session_state.user = user
                st.session_state.login_failures = 0
                st.success("Login successful.")
                st.rerun()
            else:
                st.session_state.login_failures += 1
                st.error("Invalid username or password.")

    with st.expander("Forgot password"):
        identifier = st.text_input("Enter username or university email", key="reset_identifier")
        if st.button("Create temporary password"):
            if identifier.strip():
                success, message, _ = reset_password(identifier)
                if success:
                    st.success(message)
                else:
                    st.error(message)
            else:
                st.warning("Please enter your username or email.")

def render_account_sidebar(user: dict):
    name = display_name(user)
    st.sidebar.write(f"Logged in as: **{name}**")
    st.sidebar.write(f"Role: **{user.get('role', 'unknown')}**")

    with st.sidebar.expander("Update profile"):
        new_full_name = st.text_input("Full name", value=user.get("full_name", ""), key="profile_full_name")
        new_email = st.text_input("Email", value=user.get("email") or "", key="profile_email")
        new_phone = st.text_input("Phone", value=user.get("phone") or "", key="profile_phone")
        if st.button("Save profile"):
            success, result = update_profile(user["id"], new_full_name, new_email, new_phone)
            if success:
                st.session_state.user = result
                st.success("Profile updated.")
                st.rerun()
            else:
                st.error(result)

    with st.sidebar.expander("Change password"):
        old_password = st.text_input("Old password", type="password", key="old_password")
        new_password = st.text_input("New password", type="password", key="new_password")
        confirm_password = st.text_input("Confirm password", type="password", key="confirm_password")
        if st.button("Update password"):
            if not old_password or not new_password or not confirm_password:
                st.warning("Please fill in all password fields.")
            elif new_password != confirm_password:
                st.error("New password and confirmation do not match.")
            elif len(new_password) < 6:
                st.warning("Password must contain at least 6 characters.")
            elif change_password(user["id"], old_password, new_password):
                st.success("Password updated successfully.")
            else:
                st.error("Old password is incorrect.")

    if st.sidebar.button("Logout"):
        logout()


def render_main_app():
    user = st.session_state.user
    name = display_name(user)

    render_header(
        title="Student Attendance System",
        subtitle=f"Welcome, {name}"
    )
    render_account_sidebar(user)

    role = user.get("role", "").lower()

    if role == "student":
        render_student_page(user)
    elif role == "lecturer":
        render_lecturer_page(user)
    elif role == "admin":
        page = st.sidebar.radio("Menu", ["Academic Staff", "Reports"])
        if page == "Academic Staff":
            render_admin_page(user)
        else:
            render_reports_page(user)
    else:
        st.error("Unknown role.")


if st.session_state.user is None:
    render_login_page()
else:
    render_main_app()
