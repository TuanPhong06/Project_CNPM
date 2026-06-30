import pandas as pd
import streamlit as st
from auth import hash_password
from database import get_connection
from services.report_service import get_all_sections


def add_user(username: str, password: str, full_name: str, email: str, role: str):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users(username, password_hash, full_name, email, role) VALUES (?, ?, ?, ?, ?)",
            (username, hash_password(password), full_name, email, role),
        )
        conn.commit()
        return True, "User added successfully."
    except Exception as error:
        return False, str(error)
    finally:
        conn.close()


def get_users():
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, username, full_name, email, role FROM users ORDER BY role, username"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_courses():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM courses ORDER BY course_code").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def add_course(course_code: str, course_name: str):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO courses(course_code, course_name) VALUES (?, ?)",
            (course_code, course_name),
        )
        conn.commit()
        return True, "Course added successfully."
    except Exception as error:
        return False, str(error)
    finally:
        conn.close()


def render_admin_page(user: dict):
    st.header("Academic Staff Dashboard")
    st.write(f"Welcome, **{user['full_name']}**")

    tab_users, tab_courses, tab_sections = st.tabs(
        ["Manage Users", "Manage Courses", "Monitor Sections"]
    )

    with tab_users:
        st.subheader("User List")
        users = get_users()
        st.dataframe(pd.DataFrame(users), use_container_width=True)

        st.subheader("Add New User")
        with st.form("add_user_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password", value="123456")
            full_name = st.text_input("Full name")
            email = st.text_input("Email")
            role = st.selectbox("Role", ["student", "lecturer", "admin"])
            submitted = st.form_submit_button("Add user")

        if submitted:
            if not username or not password or not full_name:
                st.warning("Username, password, and full name are required.")
            else:
                success, message = add_user(username, password, full_name, email, role)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

    with tab_courses:
        st.subheader("Course List")
        courses = get_courses()
        st.dataframe(pd.DataFrame(courses), use_container_width=True)

        st.subheader("Add New Course")
        with st.form("add_course_form"):
            course_code = st.text_input("Course code", placeholder="SE102")
            course_name = st.text_input("Course name", placeholder="Software Design")
            submitted_course = st.form_submit_button("Add course")

        if submitted_course:
            if not course_code or not course_name:
                st.warning("Course code and course name are required.")
            else:
                success, message = add_course(course_code, course_name)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

    with tab_sections:
        st.subheader("All Class Sections")
        sections = get_all_sections()
        st.dataframe(pd.DataFrame(sections), use_container_width=True)
