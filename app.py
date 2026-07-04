import streamlit as st
from auth import login, reset_password_by_email
from database import init_db
from seed_data import seed_demo_data

from pages.student_page import render_student_page
from pages.lecturer_page import render_lecturer_page
from pages.staff_page import render_staff_page

from utils.session import logout


# PAGE CONFIG 
st.set_page_config(
    page_title="Student Attendance System",
    page_icon="🎓",
    layout="wide",
)

# DATABASE 
init_db()
seed_demo_data()

# SESSION 
if "user" not in st.session_state:
    st.session_state.user = None
if "login_error" not in st.session_state:
    st.session_state.login_error = None
if "last_reset_password" not in st.session_state:
    st.session_state.last_reset_password = None

ROLE_LABELS = {
    "student": "Student",
    "lecturer": "Lecturer",
    "academic_staff": "Academic Staff",
}

# LOGIN PAGE 
def render_login_page():

    st.title("Student Attendance System")
    st.caption("Login with your university account")

    login_tab, reset_tab = st.tabs(
        ["Login", "Forgot Password"]
    )

    # LOGIN
    with login_tab:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input(
                "Password",
                type="password"
            )
            submitted = st.form_submit_button(
                "Login",
                type="primary"
            )

        if submitted:
            user = login(username, password)
            if user:
                st.session_state.user = user
                st.session_state.login_error = None
                st.success(
                    f"Welcome, {user['full_name']}."
                )
                st.rerun()
            else:
                st.session_state.login_error = (
                    "Invalid username or password."
                )
        if st.session_state.login_error:
            st.error(st.session_state.login_error)
        st.info(
            """
Demo Accounts

Student:
student01 / 123456

Lecturer:
lecturer01 / 123456

Academic Staff:
staff01 / 123456
"""
        )
    #FORGOT PASSWORD 
    with reset_tab:
        st.write(
            "Enter your university email to create a temporary password."
        )
        with st.form("reset_form"):
            email = st.text_input(
                "University Email"
            )
            reset = st.form_submit_button(
                "Create Temporary Password"
            )

        if reset:
            success, message, temp_password = (
                reset_password_by_email(email)
            )
            if success:

                st.session_state.last_reset_password = (
                    temp_password
                )
                st.success(message)
            else:
                st.session_state.last_reset_password = None
                st.error(message)
        if st.session_state.last_reset_password:
            st.warning(
                "Demo mode: Temporary password"
            )
            st.code(
                st.session_state.last_reset_password
            )

# MAIN APP 
def render_main_app():

    user = st.session_state.user
    with st.sidebar:
        st.subheader("Account")
        st.write(
            f"Name: **{user['full_name']}**"
        )
        st.write(
            f"Role: **{ROLE_LABELS[user['role']]}**"
        )
        st.divider()
        if st.button(
            "Logout",
            use_container_width=True
        ):
            logout()
            st.session_state.user = None
            st.rerun()

    #  ROLE
    if user["role"] == "student":
        render_student_page(user)
    elif user["role"] == "lecturer":
        render_lecturer_page(user)
    elif user["role"] == "academic_staff":
        render_staff_page(user)
    else:
        st.error("Unknown role.")

#START
if st.session_state.user is None:
    render_login_page()
else:
    render_main_app()
