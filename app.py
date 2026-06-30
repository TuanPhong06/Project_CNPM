import streamlit as st
from auth import login
from database import init_db
from pages.admin_page import render_admin_page
from pages.lecturer_page import render_lecturer_page
from pages.reports_page import render_reports_page
from pages.student_page import render_student_page
from seed_data import seed_demo_data
from utils.session import logout

st.set_page_config(
    page_title="Student Attendance System",
    page_icon="✅",
    layout="wide",
)

init_db()
seed_demo_data()

if "user" not in st.session_state:
    st.session_state.user = None


def render_login_page():
    st.title("Student Attendance System")
    st.caption("Python Streamlit Web GUI")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login", type="primary")

    if submitted:
        user = login(username, password)
        if user:
            st.session_state.user = user
            st.success("Login successful.")
            st.rerun()
        else:
            st.error("Invalid username or password.")

    st.info(
        "Demo accounts: student01 / 123456, student02 / 123456, "
        "lecturer01 / 123456, admin01 / 123456"
    )


def render_main_app():
    user = st.session_state.user

    with st.sidebar:
        st.write(f"Logged in as: **{user['full_name']}**")
        st.write(f"Role: **{user['role']}**")
        if st.button("Logout"):
            logout()

    if user["role"] == "student":
        render_student_page(user)
    elif user["role"] == "lecturer":
        render_lecturer_page(user)
    elif user["role"] == "admin":
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
